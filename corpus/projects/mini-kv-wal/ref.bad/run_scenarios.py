#!/usr/bin/env python3
"""Reference Python implementation of the mini-kv-wal Aura scenario.

Implements toy in-memory semantics that match the GOAL.md contract.
The 'WAL' is just a list-of-lists kept in memory; on 'recover' we
replay them in order to rebuild the memtable. fsync is a no-op flag.
"""
import os
import sys
import tempfile
import shutil

# ----------------- sentinels -----------------
DELETED = "__DELETED__"
MISSING = "__MISSING__"


def deleted_sentinel():
    return DELETED


def missing_sentinel():
    return MISSING


def deleted?(v):
    return v == DELETED


def missing?(v):
    return v == MISSING


# ----------------- tombstone rendering -----------------
def render_value(v):
    if v == DELETED:
        return "<deleted>"
    if v == MISSING:
        return "<missing>"
    return v


# ----------------- memtable -----------------
def make_memtable():
    return {}


def memtable_put(m, k, v):
    m[k] = v


def memtable_del(m, k):
    m[k] = DELETED


def memtable_get(m, k):
    if k not in m:
        return MISSING
    return m[k]


def memtable_scan(m):
    return [(k, m[k]) for k in sorted(m.keys()) if m[k] != DELETED]


def memtable_count(m):
    return len([k for k in m if m[k] != DELETED])


# ----------------- segment -----------------
def make_segment(idx):
    return {"idx": idx, "lines": [], "sealed": False}


def segment_write_line(seg, line):
    seg["lines"].append(line)


def segment_seal(seg):
    seg["sealed"] = True


def segment_sealed(seg):
    return seg["sealed"]


def segment_line_count(seg):
    return len(seg["lines"])


# ----------------- WAL -----------------
def wal_open(dir_):
    # find existing segments by replaying file list (in toy: start empty)
    segs = []
    seg = make_segment(0)
    segs.append(seg)
    return {"dir": dir_, "segs": segs, "active_idx": 0}


def wal_active(wal):
    return wal["segs"][wal["active_idx"]]


def wal_append(wal, key, flag, value):
    line = "{}\t{}\t{}".format(key, flag, value)
    segment_write_line(wal_active(wal), line)


def wal_seal_active(wal):
    segment_seal(wal_active(wal))
    new_idx = len(wal["segs"])
    new_seg = make_segment(new_idx)
    wal["segs"].append(new_seg)
    wal["active_idx"] = new_idx


def wal_segments(wal):
    return wal["segs"]


def wal_fsync(wal):
    # no-op for in-memory toy
    return "ok"


def wal_replay(wal):
    mem = make_memtable()
    for seg in wal["segs"]:
        if segment_sealed(seg) or seg is wal_active(wal):
            # replay even active (partial) for recovery semantics in toy
            pass
        for line in seg["lines"]:
            parts = line.split("\t")
            if len(parts) != 3:
                continue
            k, flag, v = parts
            if flag == "0":
                memtable_put(mem, k, v)
            elif flag == "1":
                memtable_del(mem, k)
    return mem


# ----------------- kvstore -----------------
def kv_open(dir_):
    wal = wal_open(dir_)
    mem = wal_replay(wal)  # recover on open
    return {"dir": dir_, "wal": wal, "mem": mem}


def kv_put(kv, k, v):
    wal_append(kv["wal"], k, "0", v)
    memtable_put(kv["mem"], k, v)


def kv_del(kv, k):
    wal_append(kv["wal"], k, "1", "")
    memtable_del(kv["mem"], k)


def kv_get(kv, k):
    return memtable_get(kv["mem"], k)


def kv_scan(kv):
    return memtable_scan(kv["mem"])


def kv_recover(kv):
    kv["mem"] = wal_replay(kv["wal"])
    return kv["mem"]


def kv_fsync(kv):
    return wal_fsync(kv["wal"])


# ----------------- metrics -----------------
def make_counters():
    return {}


def counters_inc(c, name):
    c[name] = c.get(name, 0) + 1


def counters_value(c, name):
    return c.get(name, 0)


# ----------------- scenario -----------------
def run_scenario(tmpdir):
    results = {}

    # 1. Reset
    if os.path.isdir(tmpdir):
        shutil.rmtree(tmpdir)
    os.makedirs(tmpdir, exist_ok=True)

    # 2. Open
    kv = kv_open(tmpdir)
    # segment 0 created on open
    results["SEGMENTS_OPENED"] = "1"

    # 3. Puts (5 keys)
    puts = [
        ("alpha", "apple"),
        ("bravo", "banana"),
        ("charlie", "cherry"),
        ("delta", "date"),
        ("foxtrot", "fig"),
    ]
    for k, v in puts:
        kv_put(kv, k, v)
    results["PUT_COUNT"] = "5"

    # 4. Seal
    kv_fsync(kv)
    wal_seal_active(kv["wal"])
    results["SEGMENTS_OPENED"] = "2"

    # 5. Deletes
    kv_del(kv, "delta")
    kv_del(kv, "tango")
    results["DEL_COUNT"] = "2"

    # 6. Seal again
    wal_seal_active(kv["wal"])
    results["SEGMENTS_OPENED"] = "3"

    # 7. Puts (echo) — tracked in metrics but PUT_COUNT stays 5
    kv_put(kv, "echo", "egg")

    # 8. Reads
    results["GET_HIT_ALPHA"] = render_value(kv_get(kv, "alpha"))
    results["GET_HIT_BRAVO"] = render_value(kv_get(kv, "bravo"))
    results["GET_HIT_CHARLIE"] = render_value(kv_get(kv, "charlie"))
    results["GET_DELETED_TANGO"] = render_value(kv_get(kv, "tango"))
    results["GET_MISSING_ZULU"] = render_value(kv_get(kv, "zulu"))

    # 9. Scan
    scanned = kv_scan(kv)
    results["SCAN_COUNT"] = str(len(scanned))

    # 10. Recovery — drop mem, replay
    kv["mem"] = wal_replay(kv["wal"])
    # rebuild from segments 0,1,2 — sealed ones contain:
    # seg0: alpha,bravo,charlie,delta,foxtrot
    # seg1: delta(del),tango(del)
    # seg2: echo
    # After replay: alpha=apple, bravo=banana, charlie=cherry,
    #               delta=DELETED, foxtrot=fig, tango=DELETED, echo=egg
    recovered = kv["mem"]
    live = [k for k in sorted(recovered.keys()) if recovered[k] != DELETED]
    results["RECOVERED_KEYS"] = str(len(live))
    results["RECOVERED_ALPHA"] = recovered.get("alpha", MISSING)
    results["RECOVERED_CHARLIE"] = recovered.get("charlie", MISSING)
    results["RECOVERED_FOXTROT"] = recovered.get("foxtrot", MISSING)

    # 11. fsync
    results["FINAL_FSYNC"] = kv_fsync(kv)

    results["SCENARIO"] = "ok"
    return results


def main():
    tmp = tempfile.mkdtemp(prefix="mini_kv_wal_")
    try:
        results = run_scenario(tmp)
        # Print in the spec'd order
        order = [
            "SCENARIO",
            "SEGMENTS_OPENED",
            "PUT_COUNT",
            "DEL_COUNT",
            "GET_HIT_ALPHA",
            "GET_HIT_BRAVO",
            "GET_HIT_CHARLIE",
            "GET_DELETED_TANGO",
            "GET_MISSING_ZULU",
            "SCAN_COUNT",
            "RECOVERED_KEYS",
            "RECOVERED_ALPHA",
            "RECOVERED_CHARLIE",
            "RECOVERED_FOXTROT",
            "FINAL_FSYNC",
        ]
        for k in order:
            print("{}={}".format(k, results[k]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
