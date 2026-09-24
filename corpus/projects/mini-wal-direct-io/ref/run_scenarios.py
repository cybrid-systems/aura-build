"""
Mini-WAL Direct-IO in-memory simulation in Python 3.
Implements the same semantics as the Aura GOAL scenario:
  - aligned direct append of fixed-size records
  - bump allocator for record slots
  - per-transaction barrier accounting
  - CRC mismatch detection on replay
  - deterministic tail recovery
"""

import sys
from typing import List, Tuple, Dict, Optional

# ---------- wal_types ----------
def wal_make_config(version: int, sector_size: int, direct: bool) -> Dict:
    return {"version": version, "sector_size": sector_size, "direct": direct}

def wal_version(cfg: Dict) -> int:
    return cfg["version"]

def wal_sector_size(cfg: Dict) -> int:
    return cfg["sector_size"]

def wal_direct(cfg: Dict) -> bool:
    return cfg["direct"]

# ---------- wal_alloc ----------
def allocator_new(slots: int) -> Dict:
    free_list = list(range(slots))
    return {"total": slots, "free": free_list}

def allocator_take(alloc: Dict) -> int:
    if not alloc["free"]:
        raise RuntimeError("allocator exhausted")
    return alloc["free"].pop(0)

def allocator_free(alloc: Dict) -> int:
    return len(alloc["free"])

def allocator_reset(alloc: Dict) -> None:
    alloc["free"] = list(range(alloc["total"]))

# ---------- wal_record ----------
def record_make(txid: int, kind: int, payload: bytes) -> Dict:
    # Layout: [txid u32][kind u32][len u32][payload...][crc u32]
    inner = (
        txid.to_bytes(4, "little")
        + kind.to_bytes(4, "little")
        + len(payload).to_bytes(4, "little")
        + payload
    )
    crc = crc32(inner)
    full = inner + crc.to_bytes(4, "little")
    return {"txid": txid, "kind": kind, "payload": payload, "crc": crc, "bytes": full}

def record_len(rec: Dict) -> int:
    return len(rec["bytes"])

def record_txid(rec: Dict) -> int:
    return rec["txid"]

def record_crc(rec: Dict) -> int:
    return rec["crc"]

# ---------- wal_crc ----------
def crc32(data: bytes) -> int:
    # Simple deterministic CRC-32 (zlib-compatible via stdlib)
    import zlib
    return zlib.crc32(data) & 0xFFFFFFFF

def crc_eq(a: int, b: int) -> bool:
    return a == b

# ---------- wal_align ----------
def align_up(n: int, base: int) -> int:
    return ((n + base - 1) // base) * base

def align_check(n: int, base: int) -> bool:
    return n % base == 0

def direct_append(buf: List[bytes], record_bytes: bytes, sector_size: int) -> int:
    # O_DIRECT style: append a padded (sector-aligned) chunk to the disk buffer.
    padded_len = align_up(len(record_bytes), sector_size)
    padded = record_bytes + b"\x00" * (padded_len - len(record_bytes))
    buf.append(padded)
    return padded_len

# ---------- wal_buffer ----------
def buffer_new(size: int) -> List[bytes]:
    return []  # list of sectors; size is the logical capacity hint

def buffer_tail(buf: List[bytes]) -> int:
    return sum(len(s) for s in buf)

def buffer_slice(buf: List[bytes], start: int, end: int) -> bytes:
    # Concatenate the buffer and slice into the byte range.
    flat = b"".join(buf)
    return flat[start:end]

def buffer_truncate(buf: List[bytes], offset: int) -> None:
    flat = b"".join(buf)
    keep = flat[:offset]
    buf.clear()
    if keep:
        buf.append(keep)

# ---------- wal_barrier ----------
def barrier_new() -> Dict:
    return {"count": 0, "bytes": 0}

def barrier_issue(br: Dict, nbytes: int) -> None:
    br["count"] += 1
    br["bytes"] += nbytes

def barrier_count(br: Dict) -> int:
    return br["count"]

def barrier_bytes(br: Dict) -> int:
    return br["bytes"]

# ---------- wal_writer ----------
def writer_open(cfg: Dict) -> Dict:
    return {"cfg": cfg, "buf": buffer_new(0), "tail": 0}

def writer_append(w: Dict, rec: Dict) -> int:
    n = direct_append(w["buf"], rec["bytes"], wal_sector_size(w["cfg"]))
    w["tail"] += n
    return n

def writer_barrier(w: Dict, br: Dict, nbytes: int) -> None:
    barrier_issue(br, nbytes)

def writer_tail(w: Dict) -> int:
    return w["tail"]

def writer_direct(w: Dict) -> bool:
    return wal_direct(w["cfg"])

# ---------- wal_replay ----------
def replay_open(buf: List[bytes], sector_size: int) -> Dict:
    flat = b"".join(buf)
    records: List[Tuple[bytes, int]] = []  # (record_bytes, record_len)
    off = 0
    # Header: 4 bytes magic then version u32, then sector-sized payload stream
    if len(flat) < 8:
        return {"buf": buf, "records": [], "i": 0, "tail": 0, "sector_size": sector_size}
    # Each record: [txid u32][kind u32][len u32][payload][crc u32] aligned to sector
    while off < len(flat):
        # Need at least 12 bytes header
        if off + 12 > len(flat):
            break
        txid = int.from_bytes(flat[off:off+4], "little")
        kind = int.from_bytes(flat[off+4:off+8], "little")
        plen = int.from_bytes(flat[off+8:off+12], "little")
        rec_len = 12 + plen + 4
        if off + rec_len > len(flat):
            break
        records.append((flat[off:off+rec_len], rec_len))
        # Advance to next sector boundary
        off += align_up(rec_len, sector_size)
    return {"buf": buf, "records": records, "i": 0, "tail": off, "sector_size": sector_size}

def replay_next(rep: Dict) -> Optional[Dict]:
    if rep["i"] >= len(rep["records"]):
        return None
    rec_bytes, _ = rep["records"][rep["i"]]
    rep["i"] += 1
    txid = int.from_bytes(rec_bytes[0:4], "little")
    kind = int.from_bytes(rec_bytes[4:8], "little")
    plen = int.from_bytes(rec_bytes[8:12], "little")
    payload = rec_bytes[12:12+plen]
    crc = int.from_bytes(rec_bytes[12+plen:12+plen+4], "little")
    return {"txid": txid, "kind": kind, "payload": payload, "crc": crc, "bytes": rec_bytes}

def replay_count(rep: Dict) -> int:
    return len(rep["records"])

def replay_tail(rep: Dict) -> int:
    return rep["tail"]

# ---------- wal_crash ----------
def crash_inject_bad_crc(buf: List[bytes], offset: int) -> None:
    # Find which sector contains the offset, then XOR a byte in that sector.
    cur = 0
    for i, sector in enumerate(buf):
        if cur <= offset < cur + len(sector):
            local = offset - cur
            data = bytearray(sector)
            data[local] ^= 0xFF
            buf[i] = bytes(data)
            return
        cur += len(sector)

# ---------- wal_report ----------
def report_build(w: Dict, alloc: Dict, br: Dict, rep: Dict) -> Dict:
    return {
        "tail": writer_tail(w),
        "barrier_count": barrier_count(br),
        "barrier_bytes": barrier_bytes(br),
        "replay_count": replay_count(rep),
        "replay_tail": replay_tail(rep),
        "alloc_free": allocator_free(alloc),
    }

# ---------- main ----------
def main() -> None:
    # 1. Build config
    cfg = wal_make_config(version=1, sector_size=4096, direct=True)

    # 2. Open direct writer
    w = writer_open(cfg)

    # 3. Allocator with 64 slots
    alloc = allocator_new(64)
    initial_free = allocator_free(alloc)

    # 4. 20-iteration append loop
    APPENDED = 0
    for i in range(20):
        slot = allocator_take(alloc)
        txid = (i % 5) + 1            # txid cycles 1..5
        kind = slot % 3
        # payload size derived from slot index so record-len varies
        payload = bytes((slot + i) & 0xFF for _ in range((slot % 32) + 1))
        rec = record_make(txid, kind, payload)
        writer_append(w, rec)
        APPENDED += 1
        # 5. barrier every 4 appends
        if (i + 1) % 4 == 0:
            writer_barrier(w, barrier_new_proxy[0], record_len(rec))  # placeholder; replaced below

    # Replace placeholder barrier with a real one (cleaner: redo barrier tracking)
    # The above placeholder appended barrier counts to a dummy; redo properly:
    # Reset writer tail & buf, allocator too? No — we want to use the SAME writer state
    # but with a proper barrier accumulator. Rebuild correctly:

def main_v2() -> None:
    cfg = wal_make_config(version=1, sector_size=4096, direct=True)
    w = writer_open(cfg)
    alloc = allocator_new(64)
    br = barrier_new()

    APPENDED = 0
    appended_rec_lens: List[int] = []
    for i in range(20):
        slot = allocator_take(alloc)
        txid = (i % 5) + 1
        kind = slot % 3
        payload = bytes((slot + i) & 0xFF for _ in range((slot % 32) + 1))
        rec = record_make(txid, kind, payload)
        writer_append(w, rec)
        APPENDED += 1
        appended_rec_lens.append(record_len(rec))
        if (i + 1) % 4 == 0:
            barrier_issue(br, record_len(rec))

    # 6. Tail offset
    tail_offset = writer_tail(w)

    # 7. Corrupt one byte mid-log
    buf = w["buf"]
    flat_len = sum(len(s) for s in buf)
    mid = flat_len // 2
    crash_inject_bad_crc(buf, mid)

    # 8. Replay
    rep = replay_open(buf, wal_sector_size(cfg))

    # Count CRC mismatches by iterating slice list
    mismatches = 0
    replayed = 0
    cur = 0
    flat = b"".join(buf)
    for rec_bytes, _rlen in rep["records"]:
        plen = int.from_bytes(rec_bytes[8:12], "little")
        body = rec_bytes[:12+plen]
        expected = int.from_bytes(rec_bytes[12+plen:12+plen+4], "little")
        got = crc32(body)
        if not crc_eq(expected, got):
            mismatches += 1

    while True:
        r = replay_next(rep)
        if r is None:
            break
        replayed += 1

    recovery_tail = replay_tail(rep)

    # 9. Recovery tail equals writer tail
    free_after = allocator_free(alloc)

    print(f"WAL_VERSION={wal_version(cfg)}")
    print(f"SECTOR_SIZE={wal_sector_size(cfg)}")
    print(f"DIRECT_ALIGNED={'true' if wal_direct(cfg) else 'false'}")
    print(f"RECORD_SLOTS={alloc['total']}")
    print(f"ALLOCATOR_FREE={free_after}")
    print(f"APPENDED_RECORDS={APPENDED}")
    print(f"BARRIERS_ISSUED={barrier_count(br)}")
    print(f"BARRIERED_BYTES={barrier_bytes(br)}")
    print(f"TAIL_OFFSET={tail_offset}")
    print(f"CRC_MISMATCHES={mismatches}")
    print(f"REPLAYED_RECORDS={replayed}")
    print(f"RECOVERY_TAIL={recovery_tail}")

# silence the dummy used in the first draft
barrier_new_proxy = [None]

if __name__ == "__main__":
    main_v2()
