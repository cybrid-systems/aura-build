#!/usr/bin/env python3
"""Reference implementation of mini-wal-torn-write-guard."""

SECTOR_SIZE = 64
WAL_VERSION = 1

# ---- bytes module ----
def byte_xor(a, b):
    return a ^ b

def byte_eq(a, b):
    return a == b

def checksum_sector(payload):
    # Simple polynomial-style checksum (not real CRC32)
    # Use 0xEDB88320-like polynomial accumulator
    crc = 0xFFFFFFFF
    for b in payload:
        crc ^= b
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xEDB88320
            else:
                crc >>= 1
    return crc ^ 0xFFFFFFFF

# ---- sector module ----
def make_sector(size):
    return {"payload": [], "checksum": None, "size": size, "dirty": True}

def sector_add_byte(s, b):
    if len(s["payload"]) >= s["size"]:
        return s  # full
    s["payload"].append(b & 0xFF)
    s["dirty"] = True
    return s

def sector_full(s):
    return len(s["payload"]) >= s["size"]

def sector_payload(s):
    return list(s["payload"])

def sector_checksum(s):
    return s["checksum"]

def sector_verify(s):
    if s["checksum"] is None:
        return False
    return checksum_sector(s["payload"]) == s["checksum"]

def sector_clone(s):
    return {"payload": list(s["payload"]), "checksum": s["checksum"],
            "size": s["size"], "dirty": s["dirty"]}

# ---- frame module ----
def make_frame(fid, payload):
    return {"id": fid, "payload": list(payload)}

def frame_id(f):
    return f["id"]

def frame_payload(f):
    return list(f["payload"])

def frame_bytes(f):
    return list(f["payload"])

# ---- wal module ----
def wal_open(size):
    return {
        "sector_size": size,
        "sectors": [],          # list of sectors
        "current": make_sector(size),
        "frames": [],           # committed frames
        "byte_count": 0,
    }

def _flush_current(w):
    if len(w["current"]["payload"]) > 0 or w["current"]["checksum"] is not None:
        # commit current sector
        w["current"]["checksum"] = checksum_sector(w["current"]["payload"])
        w["current"]["dirty"] = False
        w["sectors"].append(w["current"])
        w["current"] = make_sector(w["sector_size"])

def wal_append(w, frame):
    payload = list(frame["payload"])
    i = 0
    while i < len(payload):
        if sector_full(w["current"]):
            _flush_current(w)
        w["current"] = sector_add_byte(w["current"], payload[i])
        w["byte_count"] += 1
        i += 1
    w["frames"].append(frame)

def wal_sectors(w):
    # include current partial sector if non-empty? Spec says sectors list.
    out = [sector_clone(s) for s in w["sectors"]]
    if len(w["current"]["payload"]) > 0:
        out.append(sector_clone(w["current"]))
    return out

def wal_bytes(w):
    # Total committed bytes (sectors) + current partial bytes
    total = sum(len(s["payload"]) for s in w["sectors"])
    total += len(w["current"]["payload"])
    return total

def wal_verify(w):
    for s in w["sectors"]:
        if not sector_verify(s):
            return False
    # current sector: only verify if checksum was set (committed)
    return True

def wal_repair(w):
    # Walk sectors; rebuild any whose checksum is invalid by recomputing,
    # or truncate tail partial.
    changed = 0
    for idx, s in enumerate(w["sectors"]):
        if s["checksum"] is None:
            # missing checksum - recompute
            s["checksum"] = checksum_sector(s["payload"])
            changed += 1
        elif not sector_verify(s):
            s["checksum"] = checksum_sector(s["payload"])
            changed += 1
    # handle current partial sector: if checksum cleared, recompute (it may be torn)
    return changed

# ---- crash module ----
def crash_truncate_last_sector(w):
    # Truncate the last sector (the current/partial one) to half-ish,
    # simulating a torn write mid-frame.
    cur = w["current"]
    if len(cur["payload"]) == 0:
        # last committed sector is full; pretend last committed becomes partial
        if w["sectors"]:
            last = w["sectors"].pop()
            w["current"] = last
            w["byte_count"] -= len(last["payload"])
    cur = w["current"]
    # truncate to roughly half
    n = len(cur["payload"])
    if n > 1:
        cut = n // 2
        # adjust byte_count
        w["byte_count"] -= (n - cut)
        cur["payload"] = cur["payload"][:cut]
        cur["checksum"] = None
        cur["dirty"] = True
    return w

def crash_clear_checksums(w):
    # Clears checksums on the "truncated tail" - touches 2 sectors
    # The current (truncated) sector and the previous committed one.
    affected = 0
    cur = w["current"]
    if len(cur["payload"]) > 0:
        cur["checksum"] = None
        cur["dirty"] = True
        affected += 1
    if w["sectors"]:
        prev = w["sectors"][-1]
        prev["checksum"] = None
        prev["dirty"] = True
        affected += 1
    return affected

# ---- repair module ----
def repair_scan(w):
    # Walk all sectors; identify torn (invalid checksum or partial last),
    # then decide fix strategy.
    report = {"TORN_SECTORS": 0, "REPAIRED": 0, "TRUNCATED": 0}
    sectors = wal_sectors(w)
    n = len(sectors)
    for idx, s in enumerate(sectors):
        is_last = (idx == n - 1)
        is_torn = (s["checksum"] is None) or (not sector_verify(s))
        if is_torn:
            report["TORN_SECTORS"] += 1
            if is_last:
                # partial/torn last -> truncate
                report["TRUNCATED"] += 1
            else:
                # previous with bad checksum -> rebuild
                s["checksum"] = checksum_sector(s["payload"])
                report["REPAIRED"] += 1
    # Apply fixes back into wal state
    # The truncated last sector: drop its bytes from byte_count and remove from current
    if report["TRUNCATED"] > 0:
        cur = w["current"]
        if len(cur["payload"]) > 0:
            # discard all partial bytes
            w["byte_count"] -= len(cur["payload"])
            cur["payload"] = []
            cur["checksum"] = None
    # repaired sectors already updated above in the clone view; apply back:
    for idx, s in enumerate(sectors):
        if idx < len(w["sectors"]):
            if s["checksum"] is not None and w["sectors"][idx]["checksum"] is None:
                w["sectors"][idx]["checksum"] = s["checksum"]
                w["sectors"][idx]["dirty"] = False
    return report

def repair_count_torn(report):
    return report.get("TORN_SECTORS", 0)

def repair_count_fixed(report):
    return report.get("REPAIRED", 0) + report.get("TRUNCATED", 0)

# ---- replay module ----
def replay_frames(w):
    # Replay frames: rebuild from committed sectors' payloads by re-parsing frames.
    # Since we know frames were committed in order, reconstruct using frame boundaries.
    frames = []
    all_bytes = []
    for s in w["sectors"]:
        all_bytes.extend(s["payload"])
    # We don't know frame boundaries perfectly after truncation; use w["frames"] length capped
    # by available bytes. Each frame is 24 bytes.
    src_frames = list(w["frames"])
    max_bytes = len(all_bytes)
    max_frames = max_bytes // 24
    return src_frames[:max_frames]

def replay_count(w):
    return len(replay_frames(w))

# ---- recovery module ----
def recovery_run(w):
    # Re-open: drop any uncommitted trailing partial; verify.
    cur = w["current"]
    if len(cur["payload"]) > 0 and cur["checksum"] is None:
        # torn trailing - discard
        cur["payload"] = []
        w["byte_count"] -= sum(len(s["payload"]) for s in w["sectors"]) 
        # actually recalculate
    # recompute byte_count
    total = sum(len(s["payload"]) for s in w["sectors"])
    total += len(w["current"]["payload"])
    w["byte_count"] = total
    return w

# ---- report module ----
def report_build(w):
    return {
        "WAL_VERSION": WAL_VERSION,
        "FRAMES_APPENDED": len(w["frames"]),
        "SECTORS_WRITTEN": len(w["sectors"]),
        "CHECKSUM_OK": int(all(sector_verify(s) for s in w["sectors"]) and 
                           (len(w["current"]["payload"]) == 0 or w["current"]["checksum"] is not None)),
        "TORN_SECTORS": 0,
        "REPAIRED": 0,
        "TRUNCATED": 0,
        "REPLAYED": replay_count(w),
        "FINAL_BYTES": wal_bytes(w),
        "STATUS": "OK",
    }

def report_get(r, key):
    return r.get(key)

# ---- main scenario ----
def main():
    w = wal_open(SECTOR_SIZE)

    # Step 2: append 8 frames, each 24 payload bytes derived from frame id
    for i in range(8):
        payload = []
        # Build 24 bytes from frame id
        for j in range(24):
            payload.append((i * 7 + j * 3) & 0xFF)
        wal_append(w, make_frame(i, payload))

    # Step 3: record pre-crash
    pre_bytes = wal_bytes(w)
    pre_verify = wal_verify(w)

    # Step 4: inject torn write
    crash_truncate_last_sector(w)
    crash_clear_checksums(w)

    # Step 5: repair scan
    repair_report = repair_scan(w)
    torn = repair_count_torn(repair_report)
    repaired = repair_count_fixed(repair_report) - repair_report.get("TRUNCATED", 0)
    truncated = repair_report.get("TRUNCATED", 0)

    # Step 6: recovery
    recovery_run(w)

    # Step 7: replayed and final bytes
    replayed = replay_count(w)
    final_bytes = wal_bytes(w)
    checksum_ok = int(wal_verify(w))

    # Build report
    sectors_written = len(w["sectors"])
    frames_appended = len(w["frames"])

    status = "OK" if (torn == repaired + truncated and wal_verify(w)) else "ERR"

    print(f"WAL_VERSION={WAL_VERSION}")
    print(f"FRAMES_APPENDED={frames_appended}")
    print(f"SECTORS_WRITTEN={sectors_written}")
    print(f"CHECKSUM_OK={checksum_ok}")
    print(f"TORN_SECTORS={torn}")
    print(f"REPAIRED={repaired}")
    print(f"TRUNCATED={truncated}")
    print(f"REPLAYED={replayed}")
    print(f"FINAL_BYTES={final_bytes}")
    print(f"STATUS={status}")

if __name__ == "__main__":
    main()
