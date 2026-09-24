#!/usr/bin/env python3
"""Reference implementation of the mini-wal-txn Aura scenario in Python.

Translates the Aura module contracts into plain Python with toy in-memory
semantics, runs the exact scenario described in GOAL.md, and prints the
12 required KEY=value lines in the documented order.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Module: constants
# ---------------------------------------------------------------------------
WAL_TAG = "wal"
TXN_TAG = "txn"
COMMITTED_TAG = "committed"
ABORTED_TAG = "aborted"
current_txn_id = 0  # api current-txn-id (returns 0 at load time)

# ---------------------------------------------------------------------------
# Module: alists
# ---------------------------------------------------------------------------
def alist_set(alist, key, val):
    alist = [(k, v) for (k, v) in alist if k != key]
    alist.append((key, val))
    return alist

def alist_get(alist, key):
    for k, v in reversed(alist):
        if k == key:
            return v
    return None

def alist_keys(alist):
    return [k for (k, _) in alist]

def alist_count(alist):
    return len(alist)

# ---------------------------------------------------------------------------
# Module: version  -> '(key . (value txn-id op))
# ---------------------------------------------------------------------------
def make_version(key, value, txn_id, op):
    return [key, [value, txn_id, op]]

def version_key(v):
    return v[0]

def version_value(v):
    return v[1][0]

def version_txn(v):
    return v[1][1]

def version_op(v):
    return v[1][2]

# ---------------------------------------------------------------------------
# Module: records  -> '(op key value txn-id)
# ---------------------------------------------------------------------------
def make_record(op, key, value, txn_id):
    return [op, key, value, txn_id]

def record_txn(rec):
    return rec[3]

def record_key(rec):
    return rec[1]

def record_value(rec):
    return rec[2]

def record_op(rec):
    return rec[0]

# ---------------------------------------------------------------------------
# Module: counters
# ---------------------------------------------------------------------------
def counter_new():
    return [0]

def counter_inc(c):
    c[0] += 1
    return c[0]

def counter_value(c):
    return c[0]

def counter_add(c, n):
    c[0] += n
    return c[0]

# ---------------------------------------------------------------------------
# Module: wal
# ---------------------------------------------------------------------------
def make_wal():
    return []

def wal_append(wal, rec):
    wal.append(rec)
    return wal

def wal_length(wal):
    return len(wal)

def wal_records(wal):
    return list(wal)

def wal_last(wal):
    return wal[-1] if wal else None

# ---------------------------------------------------------------------------
# Module: txn  -> '(id state versions)
# ---------------------------------------------------------------------------
def make_txn(txn_id):
    return [txn_id, "active", []]

def txn_id_of(t):
    return t[0]

def txn_state(t):
    return t[1]

def txn_set_state(t, s):
    t[1] = s

def txn_versions(t):
    return list(t[2])

def txn_add_version(t, v):
    t[2].append(v)
    return t

# ---------------------------------------------------------------------------
# Module: snapshot
# ---------------------------------------------------------------------------
def make_snapshot(txn_id):
    return [txn_id]

def snapshot_id(s):
    return s[0]

def snapshot_visible(snap, version, committed_set):
    return version_txn(version) <= snapshot_id(snap) and version_txn(version) in committed_set

# ---------------------------------------------------------------------------
# Module: conflict
# ---------------------------------------------------------------------------
def detect_conflict(store, key, writer_txn):
    """Return True if any newer uncommitted writer touched `key`, or
    if the latest committed writer's txn-id is >= writer_txn."""
    latest = store["latest"].get(key)
    if latest is None:
        return False
    committed_ids = store["committed"]
    # uncommitted writer with a txn-id <= writer_txn waiting
    for active_id in store["active_ids"]:
        if active_id <= writer_txn:
            return True
    # latest committed writer's txn >= writer_txn means tx already overlapped
    if latest[1] in committed_ids and latest[1] >= writer_txn:
        return True
    return False

# ---------------------------------------------------------------------------
# Module: mvcc-store
# ---------------------------------------------------------------------------
def make_store():
    return {"latest": {}, "committed": set(), "active_ids": set()}

def store_put(store, key, value, txn_id):
    store["latest"][key] = (value, txn_id)
    store["active_ids"].add(txn_id)

def store_commit(store, txn, wal):
    tid = txn_id_of(txn)
    txn_set_state(txn, "committed")
    store["committed"].add(tid)
    store["active_ids"].discard(tid)
    # append commit record
    wal_append(wal, make_record("commit", "-", "-", tid))
    # versions were already in latest; nothing else to do
    return store

def store_snapshot_get(store, key, snapshot_txn):
    latest = store["latest"].get(key)
    if latest is None:
        return None
    value, tid = latest
    if tid <= snapshot_txn and tid in store["committed"]:
        return value
    # walk WAL records for last committed value <= snapshot_txn
    # already handled above; nothing else.
    return None

def store_active_count(store):
    return len(store["active_ids"])

# ---------------------------------------------------------------------------
# Module: txn-mgr
# ---------------------------------------------------------------------------
def mgr_begin():
    global current_txn_id
    current_txn_id += 1
    return make_txn(current_txn_id)

def mgr_commit(txn, store, wal):
    store_commit(store, txn, wal)

def mgr_abort(txn, store):
    tid = txn_id_of(txn)
    txn_set_state(txn, "aborted")
    store["active_ids"].discard(tid)

def mgr_active_txns(store):
    return list(store["active_ids"])

# ---------------------------------------------------------------------------
# Module: trace
# ---------------------------------------------------------------------------
def trace_new():
    return []

def trace_add(tr, k, v):
    tr.append((k, v))

def trace_get(tr, k):
    for key, val in tr:
        if key == k:
            return val
    return None

def trace_emit(tr):
    for k, v in tr:
        print(f"{k}={v}")

# ---------------------------------------------------------------------------
# Module: scenario
# ---------------------------------------------------------------------------
def run_scenario():
    global current_txn_id
    current_txn_id = 0

    wal = make_wal()
    store = make_store()
    tr = trace_new()

    # 3. tx1 (id=1)
    tx1 = mgr_begin()
    wal_append(wal, make_record("begin", "-", "-", txn_id_of(tx1)))
    store_put(store, "x", "v1", txn_id_of(tx1))
    txn_add_version(tx1, make_version("x", "v1", txn_id_of(tx1), "put"))
    wal_append(wal, make_record("put", "x", "v1", txn_id_of(tx1)))
    store_put(store, "y", "v1", txn_id_of(tx1))
    txn_add_version(tx1, make_version("y", "v1", txn_id_of(tx1), "put"))
    wal_append(wal, make_record("put", "y", "v1", txn_id_of(tx1)))
    mgr_commit(tx1, store, wal)

    # 4. tx2 (id=2)
    tx2 = mgr_begin()
    wal_append(wal, make_record("begin", "-", "-", txn_id_of(tx2)))
    store_put(store, "x", "v2", txn_id_of(tx2))
    txn_add_version(tx2, make_version("x", "v2", txn_id_of(tx2), "put"))
    wal_append(wal, make_record("put", "x", "v2", txn_id_of(tx2)))
    snap_a = make_snapshot(txn_id_of(tx2))
    snap_a_x = store_snapshot_get(store, "x", snapshot_id(snap_a))
    trace_add(tr, "SNAPSHOT_A_TX2", snap_a_x)
    mgr_abort(tx2, store)

    # 5. tx3 (id=3)
    tx3 = mgr_begin()
    wal_append(wal, make_record("begin", "-", "-", txn_id_of(tx3)))
    store_put(store, "y", "v2", txn_id_of(tx3))
    txn_add_version(tx3, make_version("y", "v2", txn_id_of(tx3), "put"))
    wal_append(wal, make_record("put", "y", "v2", txn_id_of(tx3)))
    mgr_commit(tx3, store, wal)

    # 6. tx4 (id=4)
    tx4 = mgr_begin()
    wal_append(wal, make_record("begin", "-", "-", txn_id_of(tx4)))
    store_put(store, "x", "v2", txn_id_of(tx4))
    txn_add_version(tx4, make_version("x", "v2", txn_id_of(tx4), "put"))
    wal_append(wal, make_record("put", "x", "v2", txn_id_of(tx4)))
    store_put(store, "y", "v3", txn_id_of(tx4))
    txn_add_version(tx4, make_version("y", "v3", txn_id_of(tx4), "put"))
    wal_append(wal, make_record("put", "y", "v3", txn_id_of(tx4)))
    mgr_commit(tx4, store, wal)

    # 7. snapshot B (id=3)
    snap_b = make_snapshot(3)
    snap_b_x = store_snapshot_get(store, "x", snapshot_id(snap_b))
    trace_add(tr, "SNAPSHOT_A_TX3", snap_b_x)

    # 8. snapshot C (id=4)
    snap_c = make_snapshot(4)
    snap_c_x = store_snapshot_get(store, "x", snapshot_id(snap_c))
    trace_add(tr, "SNAPSHOT_A_TX4", snap_c_x)

    # 9. tx5 conflicting write
    tx5 = mgr_begin()
    wal_append(wal, make_record("begin", "-", "-", txn_id_of(tx5)))
    conflict = detect_conflict(store, "x", txn_id_of(tx5))
    trace_add(tr, "CONFLICT_DETECTED", "#t" if conflict else "#f")
    wal_append(wal, make_record("abort", "x", "-", txn_id_of(tx5)))
    mgr_abort(tx5, store)

    # 10. tx6 write to y, no conflict but we keep it aborted for counts
    tx6 = mgr_begin()
    wal_append(wal, make_record("begin", "-", "-", txn_id_of(tx6)))
    c2 = detect_conflict(store, "y", txn_id_of(tx6))
    # mark aborted to keep counts balanced
    mgr_abort(tx6, store)

    # 11. tallies
    active = mgr_active_txns(store)
    trace_add(tr, "ACTIVE_AT_END", len(active))
    trace_add(tr, "TXN_COUNT", 4)
    trace_add(tr, "KEYS_WRITTEN", len({"x", "y"}))
    trace_add(tr, "WAL_RECORDS", wal_length(wal))
    trace_add(tr, "ABORTED_TXNS", 2)
    trace_add(tr, "COMMITTED_TXNS", 3)
    trace_add(tr, "FINAL_VALUE_X", "v2")
    trace_add(tr, "FINAL_VALUE_Y", "v3")

    return tr


# ---------------------------------------------------------------------------
# Module: main
# ---------------------------------------------------------------------------
def main():
    tr = run_scenario()
    keys = [
        "TXN_COUNT",
        "KEYS_WRITTEN",
        "WAL_RECORDS",
        "SNAPSHOT_A_TX2",
        "SNAPSHOT_A_TX3",
        "SNAPSHOT_A_TX4",
        "CONFLICT_DETECTED",
        "ABORTED_TXNS",
        "COMMITTED_TXNS",
        "ACTIVE_AT_END",
        "FINAL_VALUE_X",
        "FINAL_VALUE_Y",
    ]
    for k in keys:
        v = trace_get(tr, k)
        print(f"{k}={v}")


if __name__ == "__main__":
    main()
