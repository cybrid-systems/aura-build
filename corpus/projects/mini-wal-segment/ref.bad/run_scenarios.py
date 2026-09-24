"""
Mini-WAL-Segment toy reference implementing the GOAL scenario in pure Python.

Implements in-memory semantics for the Aura WAL Segment Manager described in
GOAL.md. When run as __main__, exercises the full append/rotate/recover/replay
flow and prints the 16 KEY=value lines from the GOAL expect list.
"""

import struct
import zlib
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


# ---------------------------------------------------------------------------
# crc32.aura
# ---------------------------------------------------------------------------

def api_crc32(data: bytes) -> int:
    return zlib.crc32(data) & 0xFFFFFFFF


def api_crc_update(crc: int, acc: int) -> int:
    # Combine two 32-bit CRCs by re-hashing acc onto crc.
    return zlib.crc32(struct.pack(">II", crc, acc)) & 0xFFFFFFFF


# ---------------------------------------------------------------------------
# page.aura
# Page layout: [magic:u32][lsn:u32][plen:u32][payload bytes][crc:u32]
# ---------------------------------------------------------------------------

PAGE_MAGIC = 0xA1A1A1A1


@dataclass
class Page:
    lsn: int
    payload: bytes
    crc: int

    def bytes(self) -> bytes:
        body = struct.pack(">III", PAGE_MAGIC, self.lsn, len(self.payload)) + self.payload
        return body + struct.pack(">I", self.crc)

    def verify(self) -> bool:
        body = struct.pack(">III", PAGE_MAGIC, self.lsn, len(self.payload)) + self.payload
        expected = zlib.crc32(body) & 0xFFFFFFFF
        return expected == self.crc


def api_make_page(lsn: int, payload: bytes) -> Page:
    body = struct.pack(">III", PAGE_MAGIC, lsn, len(payload)) + payload
    crc = zlib.crc32(body) & 0xFFFFFFFF
    return Page(lsn=lsn, payload=payload, crc=crc)


def api_page_lsn(p: Page) -> int:
    return p.lsn


def api_page_bytes(p: Page) -> bytes:
    return p.bytes()


def api_page_verify(p: Page) -> bool:
    return p.verify()


# ---------------------------------------------------------------------------
# segment.aura
# In-memory segment backed by a list of pages; tracks bytes and tail CRC.
# ---------------------------------------------------------------------------

@dataclass
class Segment:
    id: int
    path: str
    page_size: int
    pages: List[Page] = field(default_factory=list)
    bytes_used: int = 0
    fsynced: bool = False
    _corrupt_tail: bool = False

    def write(self, page: Page) -> None:
        page_bytes = page.bytes()
        if self.page_size > 0 and self.bytes_used + len(page_bytes) > self.page_size:
            raise ValueError("segment full")
        self.pages.append(page)
        self.bytes_used += len(page_bytes)
        self.fsynced = False

    def fsync(self) -> None:
        self.fsynced = True

    def tail_ok(self) -> bool:
        if self._corrupt_tail:
            return False
        return all(p.verify() for p in self.pages)


def api_make_segment(seg_id: int, path: str, page_size: int) -> Segment:
    return Segment(id=seg_id, path=path, page_size=page_size)


def api_segment_id(s: Segment) -> int:
    return s.id


def api_segment_write(s: Segment, page: Page) -> None:
    s.write(page)


def api_segment_pages(s: Segment) -> List[Page]:
    return list(s.pages)


def api_segment_bytes(s: Segment) -> int:
    return s.bytes_used


def api_segment_fsync(s: Segment) -> None:
    s.fsync()


def api_segment_tail_ok(s: Segment) -> bool:
    return s.tail_ok()


# ---------------------------------------------------------------------------
# torn_write.aura
# ---------------------------------------------------------------------------

def api_detect_torn(s: Segment) -> bool:
    if not s.pages:
        return False
    return not s.pages[-1].verify()


def api_truncate_torn(s: Segment) -> int:
    """Drop torn trailing page(s); return number of bytes truncated."""
    truncated = 0
    while s.pages and not s.pages[-1].verify():
        p = s.pages.pop()
        truncated += len(p.bytes())
        s.bytes_used -= len(p.bytes())
    return truncated


# ---------------------------------------------------------------------------
# wal_replay.aura
# ---------------------------------------------------------------------------

def api_replay_segment(s: Segment) -> Tuple[int, int]:
    """Return (lsn_of_last_good_page, bytes_restored)."""
    good_bytes = 0
    last_lsn = 0
    for p in s.pages:
        if p.verify():
            good_bytes += len(p.bytes())
            last_lsn = p.lsn
        else:
            break
    return last_lsn, good_bytes


# ---------------------------------------------------------------------------
# lsn.aura
# ---------------------------------------------------------------------------

def api_next_lsn(wal: "WAL") -> int:
    return wal.next_lsn


def api_reset_lsn(wal: "WAL") -> None:
    wal.next_lsn = 1


# ---------------------------------------------------------------------------
# stats.aura
# ---------------------------------------------------------------------------

@dataclass
class WALStats:
    seg_count: int
    bytes_appended: int
    current_lsn: int
    page_size: int
    seg0_frames: int
    seg1_frames: int
    last_frame_lsn: int
    checksum_ok: int
    recover_lsn: int
    truncated_bytes: int
    active_seg: int
    seg0_bytes: int
    seg1_bytes: int
    total_recs: int
    replay_ok: int
    crc_match: int


def api_wal_stats(wal: "WAL") -> WALStats:
    segs = wal.segments
    s0 = segs[0] if len(segs) > 0 else None
    s1 = segs[1] if len(segs) > 1 else None

    seg0_frames = len(s0.pages) if s0 else 0
    seg1_frames = len(s1.pages) if s1 else 0
    seg0_bytes = s0.bytes_used if s0 else 0
    seg1_bytes = s1.bytes_used if s1 else 0

    # Recover LSN
    rec_lsn, trunc = api_recover_wal(wal)

    # Replay seg0
    last_lsn, _ = api_replay_segment(s0) if s0 else (0, 0)

    # Total recs across segments
    total_recs = sum(len(s.pages) for s in segs)

    return WALStats(
        seg_count=len(segs),
        bytes_appended=sum(s.bytes_used for s in segs),
        current_lsn=wal.next_lsn - 1,
        page_size=wal.page_size,
        seg0_frames=seg0_frames,
        seg1_frames=seg1_frames,
        last_frame_lsn=last_lsn,
        checksum_ok=1 if (s0.tail_ok() if s0 else False) else 0,
        recover_lsn=rec_lsn,
        truncated_bytes=trunc,
        active_seg=wal.active_seg.id,
        seg0_bytes=seg0_bytes,
        seg1_bytes=seg1_bytes,
        total_recs=total_recs,
        replay_ok=1 if last_lsn > 0 else 0,
        crc_match=1 if (s0.tail_ok() if s0 else False) else 0,
    )


# ---------------------------------------------------------------------------
# recovery.aura
# ---------------------------------------------------------------------------

def api_recover_wal(wal: "WAL") -> Tuple[int, int]:
    """Walk segments from tail backwards, truncate torn pages, return (recovered_lsn, truncated_bytes)."""
    truncated = 0
    last_lsn = 0
    # Scan from oldest to newest; truncate torn pages from each tail.
    for seg in wal.segments:
        # detect torn tail
        if api_detect_torn(seg):
            truncated += api_truncate_torn(seg)
        # iterate pages from start until we hit a good one, then take last good LSN
        for p in seg.pages:
            if p.verify():
                last_lsn = p.lsn
            else:
                break
    return last_lsn, truncated


# ---------------------------------------------------------------------------
# wal.aura
# ---------------------------------------------------------------------------

@dataclass
class WAL:
    dir: str
    page_size: int
    segments: List[Segment] = field(default_factory=list)
    active_seg: Optional[Segment] = None
    next_lsn: int = 1
    seg_counter: int = 0

    def open(self) -> None:
        seg = api_make_segment(self.seg_counter, f"{self.dir}/seg{self.seg_counter}.wal", self.page_size)
        self.seg_counter += 1
        self.segments.append(seg)
        self.active_seg = seg

    def rotate(self) -> None:
        seg = api_make_segment(self.seg_counter, f"{self.dir}/seg{self.seg_counter}.wal", self.page_size)
        self.seg_counter += 1
        self.segments.append(seg)
        self.active_seg = seg


def api_wal_open(directory: str, page_size: int) -> WAL:
    w = WAL(dir=directory, page_size=page_size)
    w.open()
    return w


def api_wal_append(wal: WAL, payload: bytes) -> int:
    lsn = wal.next_lsn
    page = api_make_page(lsn, payload)
    api_segment_write(wal.active_seg, page)
    wal.next_lsn += 1
    return lsn


def api_wal_fsync(wal: WAL) -> bool:
    api_segment_fsync(wal.active_seg)
    return True


def api_wal_lsn(wal: WAL) -> int:
    return wal.next_lsn - 1


def api_wal_recover(wal: WAL) -> Tuple[int, int]:
    return api_recover_wal(wal)


def api_wal_rotate(wal: WAL) -> int:
    wal.rotate()
    return wal.active_seg.id


def api_wal_active_seg(wal: WAL) -> Segment:
    return wal.active_seg


def api_wal_segments(wal: WAL) -> List[Segment]:
    return list(wal.segments)


def api_wal_replay(wal: WAL) -> int:
    last_lsn = 0
    for seg in wal.segments:
        lsn, _ = api_replay_segment(seg)
        if lsn > last_lsn:
            last_lsn = lsn
    return last_lsn


# ---------------------------------------------------------------------------
# main.aura — scenario driver
# ---------------------------------------------------------------------------

def run_scenario() -> "WALStats":
    # 1. Open WAL with 128-byte page size.
    wal = api_wal_open("wal-dir", 128)

    # 2. Loop 42 times appending a 96-byte payload.
    payload = b"\x42" * 96
    for _ in range(42):
        api_wal_append(wal, payload)

    # 3. fsync and capture pre-rotate page count of segment 0.
    api_wal_fsync(wal)
    seg0_pages_before = len(wal.segments[0].pages)

    # 4. Force rotation.
    api_wal_rotate(wal)

    # 5. Recover — should yield LSN=42, truncated=0.
    rec_lsn, truncated = api_wal_recover(wal)

    # 6. Replay segment 0 to count frames restored.
    last_frame_lsn, _ = api_replay_segment(wal.segments[0])

    # 7. Checksum validity of segment 0.
    checksum_ok = wal.segments[0].tail_ok()

    # 8. Stats.
    stats = api_wal_stats(wal)
    return stats


def main() -> None:
    stats = run_scenario()
    print(f"SEG_COUNT={stats.seg_count}")
    print(f"BYTES_APPENDED={stats.bytes_appended}")
    print(f"CURRENT_LSN={stats.current_lsn}")
    print(f"PAGE_SIZE={stats.page_size}")
    print(f"SEG0_FRAMES={stats.seg0_frames}")
    print(f"SEG1_FRAMES={stats.seg1_frames}")
    print(f"LAST_FRAME_LSN={stats.last_frame_lsn}")
    print(f"CHECKSUM_OK={stats.checksum_ok}")
    print(f"RECOVER_LSN={stats.recover_lsn}")
    print(f"TRUNCATED_BYTES={stats.truncated_bytes}")
    print(f"ACTIVE_SEG={stats.active_seg}")
    print(f"SEG0_BYTES={stats.seg0_bytes}")
    print(f"SEG1_BYTES={stats.seg1_bytes}")
    print(f"TOTAL_RECS={stats.total_recs}")
    print(f"REPLAY_OK={stats.replay_ok}")
    print(f"CRC_MATCH={stats.crc_match}")


if __name__ == "__main__":
    main()
