#!/usr/bin/env python3
"""
Toy in-memory MVCC reader backed by an append-only WAL.
Mirrors the 13 Aura modules described in GOAL.md and prints 15 KEY=value lines.
"""

# ---------- wal-record.aura ----------
def wal_record_make(txn_id, op, key, value, prev_version):
    return {"txn": txn_id, "op": op, "key": key, "value": value, "prev": prev_version}

def wal_record_op(rec):    return rec["op"]
def wal_record_key(rec):   return rec["key"]
def wal_record_value(rec): return rec["value"]
def wal_record_txn(rec):   return rec["txn"]
def wal_record_prev(rec):  return rec["prev"]

# ---------- wal-bytes.aura ----------
def wal_bytes_encode(rec):
    # toy encoding: length-prefixed tuples via a tuple (round-trip safe)
    return ("R", rec["txn"], rec["op"], rec["key"], rec["value"], rec["prev"])

def wal_bytes_decode(b):
    assert b[0] == "R"
    _, t, o, k, v, p = b
    return {"txn": t, "op": o, "key": k, "value": v, "prev": p}

# ---------- wal-store.aura ----------
def wal_store_init():
    return {"bytes": [], "encoded": []}

def wal_store_append(store, b):
    store["bytes"].append(b)
    store["encoded"].append(b)

def wal_store_len(store):
    return len(store["bytes"])

def wal_store_ref(store, idx):
    return store["bytes"][idx]

def wal_store_bytes(store):
    # total encoded bytes — toy: tuple serialization size
    total = 0
    for b in store["bytes"]:
        if isinstance(b, tuple):
            total += 8  # tag
            for x in b[1:]:
                if isinstance(x, str):
                    total += len(x.encode("utf-8"))
                else:
                    total += 4
        else:
            total += len(str(b).encode("utf-8"))
    return total

# ---------- wal.aura ----------
def wal_append_record(store, rec):
    enc = wal_bytes_encode(rec)
    wal_store_append(store, enc)
    return wal_store_len(store) - 1  # index of new record

def wal_read_record(store, idx):
    return wal_bytes_decode(wal_store_ref(store, idx))

def wal_total_bytes(store):
    return wal_store_bytes(store)

# ---------- txn-table.aura ----------
def txn_table_init():
    return {"status": {}}  # id -> "active"|"committed"|"aborted"

def txn_table_begin(table, txn_id):
    table["status"][txn_id] = "active"

def txn_table_commit(table, txn_id):
    table["status"][txn_id] = "committed"

def txn_table_abort(table, txn_id):
    table["status"][txn_id] = "aborted"

def txn_table_status(table, txn_id):
    return table["status"].get(txn_id, "unknown")

def txn_table_active_count(table):
    return sum(1 for v in table["status"].values() if v == "active")

def txn_table_committed_count(table):
    return sum(1 for v in table["status"].values() if v == "committed")

# ---------- snapshot-table.aura ----------
def snapshot_table_init():
    return {"snaps": {}}  # snap_id -> at_txn_id

def snapshot_table_take(table, snap_id, at_txn_id):
    table["snaps"][snap_id] = at_txn_id

def snapshot_table_snap_txn(table, snap_id):
    return table["snaps"][snap_id]

def snapshot_table_count(table):
    return len(table["snaps"])

# ---------- chain-index.aura ----------
def chain_index_init():
    return {"head": {}, "lengths": {}}  # key -> head idx, key -> length

def chain_index_set(idx, key, head_idx):
    old = idx["head"].get(key)
    idx["head"][key] = head_idx
    if old is None:
        idx["lengths"][key] = 1
    else:
        idx["lengths"][key] = idx["lengths"].get(key, 1) + 1

def chain_index_get(idx, key):
    return idx["head"].get(key)

def chain_index_keys(idx):
    return list(idx["head"].keys())

def chain_index_count(idx):
    return len(idx["head"])

def chain_index_max_length(idx):
    if not idx["lengths"]:
        return 0
    return max(idx["lengths"].values())

# ---------- version-resolve.aura ----------
def version_resolve_visible(snap_txn_id, is_committed, rec):
    # visible if: committed AND rec.txn <= snap_txn_id
    if not is_committed(rec["txn"]):
        return False
    return rec["txn"] <= snap_txn_id

def version_resolve(snap_txn_id, is_committed, record_at, head_idx):
    # Walk prev-version chain; return (value-or-None, terminated-by-abort?)
    cur = head_idx
    aborted = False
    while cur is not None:
        rec = record_at(cur)
        if txn_table_status.__self__ if False else None:  # placeholder removed below
            pass
        # check abort
        # We need a way to determine if txn is aborted; peek using a callable.
        # The is_committed callable tells us commit status; we also need is_aborted.
        # We'll detect abort via is_committed False AND rec being non-final chain tip reached.
        # Instead simpler: pass through; outer resolve handles.
        break
    return cur

# Simpler correct version (replaces above):
def version_resolve_visible2(snap_txn_id, status_of, rec):
    s = status_of(rec["txn"])
    if s != "committed":
        return False
    return rec["txn"] <= snap_txn_id

def version_resolve2(snap_txn_id, status_of, record_at, head_idx):
    cur = head_idx
    while cur is not None:
        rec = record_at(cur)
        s = status_of(rec["txn"])
        if s == "committed":
            return rec, cur
        if s == "aborted":
            return None, cur  # aborted marker — not visible
        # active: keep walking (uncommitted, but visible if <= snap via eventual commit? No: not yet)
        cur = rec["prev"]
    return None, None

# ---------- mvcc-reader.aura ----------
def mvcc_reader_init(wal, chain_idx, txn_tab, snap_tab):
    return {
        "wal": wal, "chain": chain_idx, "txn": txn_tab, "snap": snap_tab,
        "stats": {"visible": 0, "not_visible": 0, "aborted": 0, "miss": 0},
    }

def mvcc_reader_update(reader, txn_id, key, value):
    # Begin txn if not already known
    if reader["txn"]["status"].get(txn_id) is None:
        txn_table_begin(reader["txn"], txn_id)
    head = chain_index_get(reader["chain"], key)
    rec = wal_record_make(txn_id, "put", key, value, head)
    idx = wal_append_record(reader["wal"], rec)
    chain_index_set(reader["chain"], key, idx)
    return idx

def mvcc_reader_get(reader, snap_id, key):
    snap_txn = snapshot_table_snap_txn(reader["snap"], snap_id)
    head = chain_index_get(reader["chain"], key)
    if head is None:
        reader["stats"]["miss"] += 1
        return None
    txn_tab = reader["txn"]
    def status_of(tid): return txn_table_status(txn_tab, tid)
    def record_at(i): return wal_read_record(reader["wal"], i)
    cur = head
    while cur is not None:
        rec = record_at(cur)
        s = status_of(rec["txn"])
        if s == "committed" and rec["txn"] <= snap_txn:
            reader["stats"]["visible"] += 1
            return rec["value"]
        cur = rec["prev"]
    # walked entire chain — determine why
    # If head's txn aborted, increment aborted; else not_visible
    head_rec = record_at(head)
    if status_of(head_rec["txn"]) == "aborted":
        reader["stats"]["aborted"] += 1
    else:
        reader["stats"]["not_visible"] += 1
    return None

def mvcc_reader_stats(reader):
    s = reader["stats"]
    return {
        "read_visible_total": s["visible"],
        "read_not_visible_total": s["not_visible"],
        "read_aborted_total": s["aborted"],
        "read_snapshot_misses": s["miss"],
    }

def mvcc_reader_finalize(reader):
    # materialize current KV by walking each chain to latest committed version
    out = {}
    for key in chain_index_keys(reader["chain"]):
        head = chain_index_get(reader["chain"], key)
        cur = head
        latest_committed = None
        while cur is not None:
            rec = wal_read_record(reader["wal"], cur)
            if txn_table_status(reader["txn"], rec["txn"]) == "committed":
                latest_committed = rec["value"]
                break
            cur = rec["prev"]
        if latest_committed is not None:
            out[key] = latest_committed
    return out

# ---------- scenario-writes.aura ----------
def scenario_build_writes(wal, chain, txn_tab):
    # Txns:
    #   t1, t2, t3, t4, t5
    # Sequence of writes building chains for keys: a, b, c
    # t1: put a=1
    # t2: put a=2, put b=1
    # t3: put b=2, put c=1   (will commit)
    # t4: put c=2             (will abort)
    # t5: put a=3             (will commit)
    mvcc_r = mvcc_reader_init(wal, chain, txn_tab, None)
    txn_table_begin(txn_tab, 1)
    mvcc_reader_update(mvcc_r, 1, "a", 1)
    txn_table_begin(txn_tab, 2)
    mvcc_reader_update(mvcc_r, 2, "a", 2)
    mvcc_reader_update(mvcc_r, 2, "b", 1)
    txn_table_begin(txn_tab, 3)
    mvcc_reader_update(mvcc_r, 3, "b", 2)
    mvcc_reader_update(mvcc_r, 3, "c", 1)
    txn_table_begin(txn_tab, 4)
    mvcc_reader_update(mvcc_r, 4, "c", 2)
    txn_table_begin(txn_tab, 5)
    mvcc_reader_update(mvcc_r, 5, "a", 3)
    # commit/abort decisions
    txn_table_commit(txn_tab, 1)
    txn_table_commit(txn_tab, 2)
    txn_table_commit(txn_tab, 3)
    txn_table_abort(txn_tab, 4)
    txn_table_commit(txn_tab, 5)
    return mvcc_r

# ---------- scenario-reads.aura ----------
def scenario_build_reads(reader, snap_tab):
    snapshot_table_take(snap_tab, "s1", 3)
    snapshot_table_take(snap_tab, "s2", 5)
    snapshot_table_take(snap_tab, "s3", 2)
    # Reads under each snapshot
    mvcc_reader_get(reader, "s1", "a")  # should see a=2 (t2)
    mvcc_reader_get(reader, "s1", "b")  # b=2 (t3)
    mvcc_reader_get(reader, "s1", "c")  # c=1 (t3)
    mvcc_reader_get(reader, "s2", "a")  # a=3 (t5)
    mvcc_reader_get(reader, "s2", "b")  # b=2
    mvcc_reader_get(reader, "s2", "c")  # c=1 (t4 aborted hides nothing — t3 already committed)
    mvcc_reader_get(reader, "s2", "d")  # miss
    mvcc_reader_get(reader, "s3", "a")  # a=2 (only t1,t2 <=2)
    mvcc_reader_get(reader, "s3", "c")  # c not yet committed at t=2 -> not_visible
    mvcc_reader_get(reader, "s1", "c")  # re-read

# ---------- scenario-stats.aura ----------
def scenario_collect(reader, wal, txn_tab, snap_tab, chain_idx):
    return {
        "wal_records_appended": wal_store_len(wal),
        "wal_bytes": wal_total_bytes(wal),
        "active_txns": txn_table_active_count(txn_tab),
        "committed_txns": txn_table_committed_count(txn_tab),
        "snapshots_created": snapshot_table_count(snap_tab),
        "keys_total": chain_index_count(chain_idx),
        "version_chains_total": chain_index_count(chain_idx),
        "chain_length_max": chain_index_max_length(chain_idx),
        "read_visible_total": mvcc_reader_stats(reader)["read_visible_total"],
        "read_not_visible_total": mvcc_reader_stats(reader)["read_not_visible_total"],
        "read_aborted_total": mvcc_reader_stats(reader)["read_aborted_total"],
        "read_snapshot_misses": mvcc_reader_stats(reader)["read_snapshot_misses"],
        "aborts_total": sum(1 for v in txn_tab["status"].values() if v == "aborted"),
        "final_kv_pairs": len(mvcc_reader_finalize(reader)),
    }

# ---------- main.aura ----------
def main_run():
    wal = wal_store_init()
    chain = chain_index_init()
    txn_tab = txn_table_init()
    snap_tab = snapshot_table_init()
    reader = scenario_build_writes(wal, chain, txn_tab)
    # reader used in writes had snap_tab=None; swap in the real one for reads
    reader["snap"] = snap_tab
    scenario_build_reads(reader, snap_tab)
    stats = scenario_collect(reader, wal, txn_tab, snap_tab, chain)
    final_kv = mvcc_reader_finalize(reader)

    print(f"WAL_RECORDS_APPENDED={stats['wal_records_appended']}")
    print(f"WAL_BYTES={stats['wal_bytes']}")
    print(f"ACTIVE_TXNS={stats['active_txns']}")
    print(f"COMMITTED_TXNS={stats['committed_txns']}")
    print(f"SNAPSHOTS_CREATED={stats['snapshots_created']}")
    print(f"KEYS_TOTAL={stats['keys_total']}")
    print(f"VERSION_CHAINS_TOTAL={stats['version_chains_total']}")
    print(f"CHAIN_LENGTH_MAX={stats['chain_length_max']}")
    print(f"READ_VISIBLE_TOTAL={stats['read_visible_total']}")
    print(f"READ_NOT_VISIBLE_TOTAL={stats['read_not_visible_total']}")
    print(f"READ_ABORTED_TOTAL={stats['read_aborted_total']}")
    print(f"READ_SNAPSHOT_MISSES={stats['read_snapshot_misses']}")
    print(f"ABORTS_TOTAL={stats['aborts_total']}")
    print(f"FINAL_KV_PAIRS={stats['final_kv_pairs']}")
    # summary line: snapshot-isolated MVCC toy summary
    summary = (
        f"summary_line="
        f"records={stats['wal_records_appended']} "
        f"chains={stats['version_chains_total']} "
        f"keys={stats['final_kv_pairs']} "
        f"visible={stats['read_visible_total']} "
        f"miss={stats['read_snapshot_misses']}"
    )
    print(summary)

if __name__ == "__main__":
    main_run()
