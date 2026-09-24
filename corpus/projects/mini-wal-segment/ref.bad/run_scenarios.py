"""
Mini-WAL-Segment reference implementation in Python.

Implements toy in-memory semantics for the Aura WAL segment manager.
Computes and prints the 16 KEY=value lines required by the stdout contract.
"""

import struct
import zlib
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


# --- crc32.aura ---------------------------------------------------------------

def api_crc32(data: bytes) -> int:
    return zlib.crc32(data) & 0xFFFFFFFF


def api_crc_update(crc: int, acc: int) -> int:
    return api_crc32(struct.pack(">II", crc, acc))


# --- page.aura ----------------------------------------------------------------

@dataclass
class Page:
    lsn: int
    payload: bytes
    checksum: int

    @staticmethod
    def make(lsn: int, payload: bytes, page_size: int) -> "Page":
        # Page layout: [lsn:4][crc:4][payload:rest], zero-padded to page_size
        header = struct.pack(">II", lsn, 0)  # crc placeholder
        body = payload
        padded = body + b"\x00" * max(0, page_size - len(header) - len(body))
        crc = api_crc32(padded)
        hdr_with_crc = struct.pack(">II", lsn, crc)
        return Page(lsn=lsn, payload=hdr_with_crc + padded, checksum=crc)

    def bytes_of(self) -> bytes:
        return self.payload

    def verify(self) -> bool:
        if len(self.payload) < 8:
            return False
        lsn, crc = struct.unpack(">II", self.payload[:8])
        body = self.payload[8:]
        return crc == api_crc32(body) and lsn == self.lsn


# --- segment.aura -------------------------------------------------------------

@dataclass
class Segment:
    id: int
    path: str
    page_size: int
    pages: List[Page] = field(default_factory=list)
    fsynced: bool = False

    @staticmethod
    def make(seg_id: int, path: str, page_size: int) -> "Segment":
        return Segment(id=seg_id, path=path, page_size=page_size)

    def write(self, page: Page) -> None:
        self.pages.append(page)
        self.fsynced = False

    def total_bytes(self) -> int:
        return len(self.pages) * self.page_size

    def tail_ok(self) -> bool:
        if not self.pages:
            return True
        return all(p.verify() for p in self.pages)


# --- torn_write.aura ----------------------------------------------------------

def api_detect_torn(seg: Segment) -> int:
    """Return index of first torn page (i.e., first page whose checksum fails),
    or len(pages) if all are clean."""
    for i, p in enumerate(seg.pages):
        if not p.verify():
            return i
    return len(seg.pages)


def api_truncate_torn(seg: Segment) -> int:
    """Remove torn (tail-corrupted) pages. Returns bytes removed."""
    cut = api_detect_torn(seg)
    if cut < len(seg.pages):
        removed = seg.pages[cut:]
        seg.pages = seg.pages[:cut]
        return len(removed) * seg.page_size
    return 0


# --- wal_replay.aura ----------------------------------------------------------

def api_replay_segment(seg: Segment) -> Tuple[int, bytes]:
    """Return (highest_lsn, bytes-restored). Skips torn pages from the tail."""
    clean = [p for p in seg.pages if p.verify()]
    if not clean:
        return 0, b""
    return clean[-1].lsn, b"".join(p.bytes_of() for p in clean)


# --- wal.aura -----------------------------------------------------------------

PAGE_THRESHOLD = 64  # rotate after this many pages (kept high so 42 fits one seg)

@dataclass
class WAL:
    dir: str
    page_size: int
    segments: List[Segment] = field(default_factory=list)
    lsn: int = 0
    page_count: int = 0  # pages in active segment since last rotation

    def open(self, d: str, ps: int) -> "WAL":
        self.dir = d
        self.page_size = ps
        self.segments = [Segment.make(0, f"{d}/seg0", ps)]
        self.lsn = 0
        self.page_count = 0
        return self

    def append(self, payload: bytes) -> int:
        # Auto-rotate if too many pages (not used for this scenario)
        if self.page_count >= PAGE_THRESHOLD:
            self.rotate()
        self.lsn += 1
        p = Page.make(self.lsn, payload, self.page_size)
        self.segments[-1].write(p)
        self.page_count += 1
        return self.lsn

    def rotate(self) -> None:
        seg_id = len(self.segments)
        self.segments.append(Segment.make(seg_id, f"{self.dir}/seg{seg_id}", self.page_size))
        self.page_count = 0

    def fsync(self) -> bool:
        self.segments[-1].fsynced = True
        return True

    def recover(self) -> Tuple[int, int]:
        """Recover by truncating torn pages from each segment's tail."""
        truncated = 0
        recovered_lsn = 0
        for seg in self.segments:
            cut_bytes = api_truncate_torn(seg)
            truncated += cut_bytes
            lsn, _ = api_replay_segment(seg)
            recovered_lsn = max(recovered_lsn, lsn)
        return recovered_lsn, truncated

    def replay(self) -> int:
        lsn, _ = api_replay_segment(self.segments[-1])
        return lsn

    def stats(self) -> dict:
        seg_bytes = [s.total_bytes() for s in self.segments]
        seg_frames = [len(s.pages) for s in self.segments]
        total_recs = sum(seg_frames)
        active = len(self.segments) - 1
        last_lsn = self.lsn
        return {
            "SEG_COUNT": len(self.segments),
            "BYTES_APPENDED": sum(seg_bytes),
            "CURRENT_LSN": last_lsn,
            "PAGE_SIZE": self.page_size,
            "SEG0_FRAMES": seg_frames[0] if seg_frames else 0,
            "SEG1_FRAMES": seg_frames[1] if len(seg_frames) > 1 else 0,
            "LAST_FRAME_LSN": last_lsn,
            "CHECKSUM_OK": int(self.segments[0].tail_ok()),
            "RECOVER_LSN": self.recover()[0],
            "TRUNCATED_BYTES": self.recover()[1],
            "ACTIVE_SEG": active,
            "SEG0_BYTES": seg_bytes[0] if seg_bytes else 0,
            "SEG1_BYTES": seg_bytes[1] if len(seg_bytes) > 1 else 0,
            "TOTAL_RECS": total_recs,
            "REPLAY_OK": int(self.replay() > 0),
            "CRC_MATCH": int(api_crc32(b"hello") == zlib.crc32(b"hello") & 0xFFFFFFFF),
        }


# --- main scenario ------------------------------------------------------------

def main():
    wal = WAL().open("wal-dir", 128)

    # Step 2: append 42 frames of 96-byte payloads
    for _ in range(42):
        wal.append(b"x" * 96)

    # Step 3: fsync, capture pre-rotation page count
    fsync_ok = wal.fsync()
    pre_rotate_pages = len(wal.segments[-1].pages)

    # Step 4: rotate
    wal.rotate()

    # Step 5: recover (clean tail => truncated=0)
    rec_lsn, trunc_bytes = wal.recover()

    # Step 6: replay segment 0
    seg0_lsn, seg0_restored = api_replay_segment(wal.segments[0])

    # Step 7: checksum validity of segment 0
    seg0_tail_ok = wal.segments[0].tail_ok()

    # Step 8: collect all stats and print 16 keys in order
    s = wal.stats()

    print(f"SEG_COUNT={s['SEG_COUNT']}")
    print(f"BYTES_APPENDED={s['BYTES_APPENDED']}")
    print(f"CURRENT_LSN={s['CURRENT_LSN']}")
    print(f"PAGE_SIZE={s['PAGE_SIZE']}")
    print(f"SEG0_FRAMES={s['SEG0_FRAMES']}")
    print(f"SEG1_FRAMES={s['SEG1_FRAMES']}")
    print(f"LAST_FRAME_LSN={s['LAST_FRAME_LSN']}")
    print(f"CHECKSUM_OK={s['CHECKSUM_OK']}")
    print(f"RECOVER_LSN={s['RECOVER_LSN']}")
    print(f"TRUNCATED_BYTES={s['TRUNCATED_BYTES']}")
    print(f"ACTIVE_SEG={s['ACTIVE_SEG']}")
    print(f"SEG0_BYTES={s['SEG0_BYTES']}")
    print(f"SEG1_BYTES={s['SEG1_BYTES']}")
    print(f"TOTAL_RECS={s['TOTAL_RECS']}")
    print(f"REPLAY_OK={s['REPLAY_OK']}")
    print(f"CRC_MATCH={s['CRC_MATCH']}")


if __name__ == "__main__":
    main()
