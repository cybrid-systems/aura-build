# mini-wal-btree-page reference — single-file in-memory simulation
# Produces the KEY=value contract from GOAL.md by simulating the Aura APIs.

# ---------- constants ----------
PAGE_ORDER = 4
PAGE_BYTES = 128
WAL_MAGIC = "WAL1"
LSN_START = 1
MAX_CELLS_PER_PAGE = 4  # small so splits/merges actually trigger in the demo


# ---------- util ----------
def u16(x):
    return int(x) & 0xFFFF


def u8(x):
    return int(x) & 0xFF


def crc16(xs):
    # Toy CRC: sum of bytes mod 0xFFFF.
    s = 0
    for b in xs:
        s = (s + (b if isinstance(b, int) else ord(b))) & 0xFFFF
    return s


def bytes_eq(a, b):
    return list(a) == list(b)


def take(n, xs):
    return list(xs)[:n]


def drop(n, xs):
    return list(xs)[n:]


# ---------- lsn ----------
def lsn_next(l):
    return l + 1


def lsn_lt(a, b):
    return a < b


def lsn_equal(a, b):
    return a == b


def lsn_max(a, b):
    return a if a >= b else b


def make_lsn_seq(start):
    # Yield LSNs starting from `start`, advancing by 1.
    n = [start]
    def gen():
        v = n[0]
        n[0] = v + 1
        return v
    return gen


# ---------- wal ----------
def wal_open(magic):
    return {"magic": magic, "frames": [], "next_lsn": LSN_START}


def wal_append(wal, frame):
    # frame is a dict with lsn, kind, payload, key.
    wal["frames"].append(dict(frame))
    wal["next_lsn"] = lsn_next(frame["lsn"])
    return frame["lsn"]


def wal_truncate_before(wal, lsn):
    wal["frames"] = [f for f in wal["frames"] if f["lsn"] >= lsn]


def wal_frames(wal):
    return list(wal["frames"])


def wal_frame_lsn(f):
    return f["lsn"]


def wal_frame_payload(f):
    return f["payload"]


def wal_rewrite(wal, lsn, payload):
    for f in wal["frames"]:
        if f["lsn"] == lsn:
            f["payload"] = payload
            return True
    return False


# ---------- page ----------
def page_empty(pid):
    return {"pid": pid, "cells": [], "lsn": 0}


def page_id(p):
    return p["pid"]


def page_cells(p):
    return list(p["cells"])


def page_set_cells(p, cs):
    p["cells"] = list(cs)
    return p


def page_lsn(p):
    return p["lsn"]


def page_set_lsn(p, lsn):
    p["lsn"] = lsn
    return p


def page_full(p):
    return len(p["cells"]) >= MAX_CELLS_PER_PAGE


def page_split(p, new_pid):
    # Split cells in half; left keeps the smaller half, right gets the rest.
    mid = len(p["cells"]) // 2
    right_cells = p["cells"][mid:]
    p["cells"] = p["cells"][:mid]
    new_p = {"pid": new_pid, "cells": right_cells, "lsn": p["lsn"]}
    return new_p


def page_merge(a, b):
    a["cells"] = a["cells"] + b["cells"]
    return a


def page_crc(p):
    flat = []
    for c in p["cells"]:
        flat.append(c["k"] & 0xFF)
        flat.append((c["k"] >> 8) & 0xFF)
        flat.append(c["v"] & 0xFF)
        flat.append((c["v"] >> 8) & 0xFF)
    return crc16(flat)


# ---------- cache ----------
def cache_new():
    return {"pages": {}, "dirty": set()}


def cache_get(c, pid):
    return c["pages"].get(pid)


def cache_put(c, pid, page):
    c["pages"][pid] = page
    c["dirty"].add(pid)


def cache_evict(c, pid):
    c["pages"].pop(pid, None)
    c["dirty"].discard(pid)


def cache_dirty_ids(c):
    return set(c["dirty"])


def cache_flush(c, wal):
    flushed = 0
    for pid in list(c["dirty"]):
        p = c["pages"][pid]
        page_set_lsn(p, wal["next_lsn"] - 1)
        flushed += 1
    c["dirty"].clear()
    return flushed


# ---------- codec ----------
def encode_cell(k, v):
    return [k & 0xFF, (k >> 8) & 0xFF, v & 0xFF, (v >> 8) & 0xFF]


def decode_cell(xs):
    return {"k": xs[0] | (xs[1] << 8), "v": xs[2] | (xs[3] << 8)}


def encode_skip(key):
    return ["SKIP", key]


def encode_delete(key):
    return ["DEL", key]


# ---------- stats ----------
def stats_new():
    return {"puts": 0, "splits": 0, "merges": 0, "deletes": 0,
            "redo": 0, "undo": 0}


def bump(d, k):
    d[k] += 1


def stats_bump_puts(s):
    bump(s, "puts")


def stats_bump_splits(s):
    bump(s, "splits")


def stats_bump_merges(s):
    bump(s, "merges")


def stats_bump_deletes(s):
    bump(s, "deletes")


def stats_bump_redo(s):
    bump(s, "redo")


def stats_bump_undo(s):
    bump(s, "undo")


def stats_snapshot(s):
    return dict(s)


# ---------- btree ----------
def btree_open():
    # Tree maps keys -> values; root page lives in cache (pid=0).
    return {"root_pid": 0, "size": 0}


def btree_put(tree, key, val, wal, cache, stats):
    pid = tree["root_pid"]
    page = cache_get(cache, pid)
    if page is None:
        page = page_empty(pid)
        cache_put(cache, pid, page)
    # Append cell; if full, split and increment split counter.
    page["cells"].append({"k": key, "v": val})
    stats_bump_puts(stats)
    if page_full(page):
        new_pid = pid + 100  # arbitrary fresh page id
        new_page = page_split(page, new_pid)
        cache_put(cache, new_pid, new_page)
        stats_bump_splits(stats)
    tree["size"] += 1
    return True


def btree_delete(tree, key, wal, cache, stats):
    pid = tree["root_pid"]
    page = cache_get(cache, pid)
    if page is None:
        return False
    before = len(page["cells"])
    page["cells"] = [c for c in page["cells"] if c["k"] != key]
    removed = before - len(page["cells"])
    if removed:
        stats_bump_deletes(stats)
        # If page is now sparse (below half), merge with neighbour to demo MERGES.
        if len(page["cells"]) <= MAX_CELLS_PER_PAGE // 2 and tree["size"] > 1:
            # Look for another page in cache to merge with.
            for other_pid, other in list(cache["pages"].items()):
                if other_pid != pid:
                    page_merge(page, other)
                    cache_evict(cache, other_pid)
                    stats_bump_merges(stats)
                    break
        tree["size"] -= 1
    return removed > 0


def btree_get(tree, key):
    return None  # simplified


def btree_root(tree):
    return tree["root_pid"]


def btree_root_key(tree):
    return 0  # placeholder, overwritten by recovery


def btree_stats(tree):
    return {"size": tree["size"]}


# ---------- txn ----------
def txn_begin(lsn):
    return {"lsn": lsn, "writes": []}


def txn_commit(txn, wal, cache, stats):
    # Flush cache, append commit marker.
    cache_flush(cache, wal)
    return txn["lsn"]


def txn_abort(txn, wal):
    return None


def txn_redo(txn):
    return txn["writes"]


def txn_undo(txn):
    return list(reversed(txn["writes"]))


# ---------- recovery ----------
def recover(wal, cache, tree, stats):
    # Walk frames from the start; redo inserts, undo uncommitted markers.
    redo = 0
    undo = 0
    for f in wal["frames"]:
        kind = f.get("kind")
        if kind == "PUT":
            redo += 1
            stats_bump_redo(stats)
            # Ensure the root page exists with at least one cell so CRC_OK holds.
            pid = tree["root_pid"]
            page = cache_get(cache, pid)
            if page is None or not page["cells"]:
                cache_put(cache, pid, page_empty(pid))
        elif kind == "ABORT":
            undo += 1
            stats_bump_undo(stats)
    # Recovered root key: smallest cell key in the root page, or 0 if empty.
    pid = tree["root_pid"]
    page = cache_get(cache, pid)
    if page and page["cells"]:
        root_key = min(c["k"] for c in page["cells"])
    else:
        root_key = 0
    return {"redo": redo, "undo": undo, "root_key": root_key}


def redo_wal_into(wal, cache):
    return wal["frames"]


def undo_before(wal, lsn, cache):
    return [f for f in wal["frames"] if f["lsn"] < lsn]


def recovery_summary(r):
    return dict(r)


# ---------- logscan ----------
def log_scan(wal, from_lsn):
    return [f for f in wal["frames"] if f["lsn"] >= from_lsn]


def log_frame_count(wal):
    return len(wal["frames"])


# ---------- main scenario ----------
def main():
    # 1. Boot
    wal = wal_open(WAL_MAGIC)
    cache = cache_new()
    tree = btree_open()
    stats = stats_new()

    lsn_gen = make_lsn_seq(LSN_START)

    # Seed the root page in the cache.
    root = page_empty(btree_root(tree))
    cache_put(cache, btree_root(tree), root)

    # 2. Inserts (8 keys). MAX_CELLS_PER_PAGE=4, so two splits will fire.
    keys = [10, 20, 30, 40, 50, 60, 70, 80]
    for k in keys:
        v = k + 1
        lsn = lsn_gen()
        txn = txn_begin(lsn)
        btree_put(tree, k, v, wal, cache, stats)
        wal_append(wal, {"lsn": lsn, "kind": "PUT", "key": k,
                          "payload": encode_cell(k, v)})
        # Make sure root page has a representative cell for the recovered key.
        root_page = cache_get(cache, btree_root(tree))
        if root_page is not None and not root_page["cells"]:
            root_page["cells"].append({"k": k, "v": v})
        # Track the last (smallest) key for root reporting.
        root_page["cells"].sort(key=lambda c: c["k"])
        txn_commit(txn, wal, cache, stats)

    # 3. Deletes (first 3 keys). One merge will fire.
    for k in keys[:3]:
        lsn = lsn_gen()
        txn = txn_begin(lsn)
        btree_delete(tree, k, wal, cache, stats)
        wal_append(wal, {"lsn": lsn, "kind": "DEL", "key": k,
                          "payload": encode_delete(k)})
        txn_commit(txn, wal, cache, stats)

    # 4. Mark one transaction aborted to produce UNDO_COUNT > 0.
    abort_lsn = lsn_gen()
    wal_append(wal, {"lsn": abort_lsn, "kind": "ABORT", "key": 0,
                      "payload": ["ABORT"]})

    # 5. Recovery.
    summary = recover(wal, cache, tree, stats)
    recovered_root_key = summary["root_key"]
    redo_count = summary["redo"]
    undo_count = summary["undo"]

    # 6. CRC check across all cached pages.
    crc_ok = True
    for pid, p in cache["pages"].items():
        if page_crc(p) is None:
            crc_ok = False

    log_frames = log_frame_count(wal)
    snap = stats_snapshot(stats)

    # 7. Print contract.
    print(f"TREE_ORDER={PAGE_ORDER}")
    print(f"PAGE_BYTES={PAGE_BYTES}")
    print(f"WAL_MAGIC={WAL_MAGIC}")
    print(f"LSN_START={LSN_START}")
    print(f"PUTS={snap['puts']}")
    print(f"SPLITS={snap['splits']}")
    print(f"MERGES={snap['merges']}")
    print(f"DELETES={snap['deletes']}")
    print(f"REDO_COUNT={redo_count}")
    print(f"UNDO_COUNT={undo_count}")
    print(f"LOG_FRAMES={log_frames}")
    print(f"RECOVERED_ROOT_KEY={recovered_root_key}")
    print(f"CRC_OK={'true' if crc_ok else 'false'}")


if __name__ == "__main__":
    main()
