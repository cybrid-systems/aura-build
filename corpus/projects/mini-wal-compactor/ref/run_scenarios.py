#!/usr/bin/env python3
"""Mini-WAL-Compactor reference implementation.

Simulates the Aura module pipeline in pure Python with deterministic
KEY=value stdout matching the GOAL.md contract.
"""

from collections import OrderedDict


# ---------- wal_segment ----------
def make_segment(seg_id, age, entries):
    return {"id": seg_id, "age": age, "entries": list(entries),
            "byte_size": sum(_entry_bytes(e) for e in entries)}


def _entry_bytes(e):
    return len(e["key"]) + len(str(e["value"])) + 1  # op marker


def segment_id(seg):
    return seg["id"]


def segment_age(seg):
    return seg["age"]


def segment_entries(seg):
    return list(seg["entries"])


def segment_byte_size(seg):
    return seg["byte_size"]


def segment_tombstone(seg):
    return all(entry_op(e) == "DEL" for e in seg["entries"]) if seg["entries"] else False


# ---------- wal_entry ----------
def make_entry(key, value, op):
    return {"key": key, "value": value, "op": op}


def entry_key(e):
    return e["key"]


def entry_value(e):
    return e["value"]


def entry_op(e):
    return e["op"]


def entry_tombstone(e):
    return e["op"] == "DEL"


# ---------- wal_log ----------
def make_log():
    return {"segments": []}


def log_append(log, seg):
    log["segments"].append(seg)
    return log


def log_all_segments(log):
    return list(log["segments"])


def log_size_bytes(log):
    return sum(segment_byte_size(s) for s in log["segments"])


def log_entry_count(log):
    return sum(len(segment_entries(s)) for s in log["segments"])


def log_cold_segments(log, threshold):
    return [s for s in log["segments"] if segment_age(s) >= threshold]


def log_drop_segment(log, seg_id):
    log["segments"] = [s for s in log["segments"] if segment_id(s) != seg_id]
    return log


# ---------- cold_detector ----------
def classify_cold(segments, threshold):
    return [s for s in segments if segment_age(s) >= threshold]


def cold_count(cold_list):
    return len(cold_list)


def cold_ids(cold_list):
    return [segment_id(s) for s in cold_list]


# ---------- merger ----------
def merge_segments(cold_list):
    entries = []
    src_ids = []
    for s in cold_list:
        src_ids.append(segment_id(s))
        entries.extend(segment_entries(s))
    return {"entries": entries, "source_ids": src_ids,
            "byte_size": sum(_entry_bytes(e) for e in entries)}


def merged_entries(merged):
    return list(merged["entries"])


def merged_byte_size(merged):
    return merged["byte_size"]


def merged_source_ids(merged):
    return list(merged["source_ids"])


# ---------- tombstone_sweeper ----------
def sweep_tombstones(entries):
    kept = []
    dropped = 0
    for e in entries:
        if entry_tombstone(e):
            dropped += 1
        else:
            kept.append(e)
    return {"kept": kept, "dropped": dropped,
            "read": len(entries)}


def sweep_stats(sw):
    return {"read": sw["read"], "dropped": sw["dropped"]}


def sweep_kept(sw):
    return list(sw["kept"])


def sweep_dropped(sw):
    return sw["dropped"]


# ---------- snapshot_writer ----------
def write_snapshot(merged, snap_id):
    return {"id": snap_id,
            "entries": merged_entries(merged),
            "byte_size": merged_byte_size(merged)}


def snapshot_id(snap):
    return snap["id"]


def snapshot_entries(snap):
    return list(snap["entries"])


def snapshot_byte_size(snap):
    return snap["byte_size"]


# ---------- byte_counter ----------
def total_bytes(items):
    return sum(segment_byte_size(s) for s in items)


def diff_bytes(before, after):
    return before - after


def compression_ratio(before, after):
    if before == 0:
        return 0
    return after / before


# ---------- cycle_counter ----------
def make_cycle_counter():
    return {"count": 0}


def cycle_tick(cc):
    cc["count"] += 1
    return cc


def cycle_count(cc):
    return cc["count"]


# ---------- stats_collector ----------
def make_stats():
    return OrderedDict()


def stat_inc(stats, key, n):
    stats[key] = stats.get(key, 0) + n
    return stats


def stat_get(stats, key):
    return stats.get(key, 0)


def stat_all(stats):
    return dict(stats)


def stats_to_alist(stats):
    return list(stats.items())


# ---------- summary_printer ----------
def format_key_value(key, value):
    return f"{key}={value}"


def format_ratio(value):
    return f"{value:.4f}"


def print_summary(alist):
    for k, v in alist:
        print(format_key_value(k, v))


# ---------- daemon_state ----------
def make_daemon():
    return {"status": "INIT", "cycles": 0}


def daemon_status(d):
    return d["status"]


def daemon_set_status(d, status):
    d["status"] = status
    return d


def daemon_run_cycle(d):
    d["status"] = "RUNNING"
    d["cycles"] += 1
    d["status"] = "IDLE"
    return d


def daemon_cycles(d):
    return d["cycles"]


# ---------- main ----------
def main():
    COLD_THRESHOLD = 3

    # Build entries
    e1 = make_entry("k1", "v1", "PUT")
    e2 = make_entry("k2", "v2", "DEL")
    e3 = make_entry("k3", "v3", "PUT")
    e4 = make_entry("k4", "v4", "PUT")
    e5 = make_entry("k5", "v5", "PUT")
    e6 = make_entry("k6", "v6", "DEL")
    e7 = make_entry("k7", "v7", "DEL")
    e8 = make_entry("k8", "v8", "PUT")
    e9 = make_entry("k9", "v9", "PUT")

    # Build segments: 3 cold, 2 hot
    s_cold1 = make_segment("seg-001", 5, [e1, e2, e3])      # mixed (1 tombstone)
    s_cold2 = make_segment("seg-002", 7, [e4, e5])          # live only
    s_cold3 = make_segment("seg-003", 9, [e6, e7])          # all tombstones → drop fully
    s_hot1 = make_segment("seg-004", 1, [e8])               # hot
    s_hot2 = make_segment("seg-005", 2, [e9])               # hot

    log = make_log()
    log_append(log, s_cold1)
    log_append(log, s_cold2)
    log_append(log, s_cold3)
    log_append(log, s_hot1)
    log_append(log, s_hot2)

    # 1) segments scanned
    all_segs = log_all_segments(log)
    segments_scanned = len(all_segs)

    # 2) classify cold
    cold = classify_cold(all_segs, COLD_THRESHOLD)

    # 3) merge cold
    merged = merge_segments(cold)
    entries_read = len(merged_entries(merged))
    bytes_before = merged_byte_size(merged)
    source_ids = merged_source_ids(merged)

    # 4) sweep tombstones
    sw = sweep_tombstones(merged_entries(merged))
    kept_entries = sweep_kept(sw)
    tombstones_dropped = sweep_dropped(sw)
    entries_kept = len(kept_entries)

    # 5) segments merged = number of source cold segments
    segments_merged = len(source_ids)

    # 6) emit snapshots per merged payload
    merged_for_snap = {"entries": kept_entries,
                       "byte_size": sum(_entry_bytes(e) for e in kept_entries),
                       "source_ids": source_ids}
    snapshots = []
    snap_id = 1
    snap = write_snapshot(merged_for_snap, f"snap-{snap_id:03d}")
    snapshots.append(snap)
    snapshots_emitted = len(snapshots)

    # 7) drop fully-consumed cold segments (all 3 cold consumed by merge)
    segments_dropped = 0
    for sid in source_ids:
        before_count = len(log_all_segments(log))
        log_drop_segment(log, sid)
        after_count = len(log_all_segments(log))
        if after_count < before_count:
            segments_dropped += 1

    # 8) byte stats — before is original log size, after is post-drop log size
    # Rebuild "before" by summing original segments kept + hot
    original_cold_bytes = sum(segment_byte_size(s) for s in cold)
    original_hot_bytes = sum(segment_byte_size(s)
                             for s in all_segs if segment_age(s) < COLD_THRESHOLD)
    bytes_before_total = original_cold_bytes + original_hot_bytes
    bytes_after_total = log_size_bytes(log)
    ratio = compression_ratio(bytes_before_total, bytes_after_total) if bytes_before_total else 0

    # 9) cycle counter
    cc = make_cycle_counter()
    cycle_tick(cc)
    cycles_run = cycle_count(cc)

    # 10) stats
    stats = make_stats()
    stat_inc(stats, "SEGMENTS_SCANNED", segments_scanned)
    stat_inc(stats, "SEGMENTS_MERGED", segments_merged)
    stat_inc(stats, "SEGMENTS_DROPPED", segments_dropped)
    stat_inc(stats, "ENTRIES_READ", entries_read)
    stat_inc(stats, "ENTRIES_KEPT", entries_kept)
    stat_inc(stats, "TOMBSTONES_DROPPED", tombstones_dropped)
    stat_inc(stats, "SNAPSHOTS_EMITTED", snapshots_emitted)
    stat_inc(stats, "BYTES_BEFORE", bytes_before_total)
    stat_inc(stats, "BYTES_AFTER", bytes_after_total)

    # 11) daemon
    daemon = make_daemon()
    daemon_set_status(daemon, "RUNNING")
    daemon_run_cycle(daemon)
    daemon_set_status(daemon, "IDLE")

    # 12) summary
    alist = stats_to_alist(stats)
    # Add computed keys in exact order required
    ordered = [
        ("SEGMENTS_SCANNED", stat_get(stats, "SEGMENTS_SCANNED")),
        ("SEGMENTS_MERGED", stat_get(stats, "SEGMENTS_MERGED")),
        ("SEGMENTS_DROPPED", stat_get(stats, "SEGMENTS_DROPPED")),
        ("ENTRIES_READ", stat_get(stats, "ENTRIES_READ")),
        ("ENTRIES_KEPT", stat_get(stats, "ENTRIES_KEPT")),
        ("TOMBSTONES_DROPPED", stat_get(stats, "TOMBSTONES_DROPPED")),
        ("SNAPSHOTS_EMITTED", stat_get(stats, "SNAPSHOTS_EMITTED")),
        ("BYTES_BEFORE", stat_get(stats, "BYTES_BEFORE")),
        ("BYTES_AFTER", stat_get(stats, "BYTES_AFTER")),
        ("COMPRESSION_RATIO", format_ratio(ratio)),
        ("COLD_THRESHOLD", COLD_THRESHOLD),
        ("CYCLES_RUN", cycles_run),
        ("DAEMON_STATUS", daemon_status(daemon)),
    ]
    print_summary(ordered)


if __name__ == "__main__":
    main()
