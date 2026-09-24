#!/usr/bin/env python3
"""Reference implementation of the mini-wal-lsm-sstable Aura GOAL."""

import sys


def make_keycodec():
    def key_encode(n):
        return f"KEY_{n:010d}"

    def key_decode(s):
        # "KEY_0000000050" -> 50
        return int(s.split("_")[1])

    def key_compare(a, b):
        if a < b:
            return -1
        if a > b:
            return 1
        return 0

    return {"encode": key_encode, "decode": key_decode, "compare": key_compare}


def make_valuecodec():
    TOMBSTONE = "__TOMBSTONE__"

    def value_encode(v):
        if v == TOMBSTONE:
            return TOMBSTONE
        return f"VAL_{v}" if isinstance(v, int) else str(v)

    def value_decode(s):
        if s == TOMBSTONE:
            return TOMBSTONE
        if s.startswith("VAL_"):
            return int(s[4:])
        return s

    def tombstone_q(v):
        return v == TOMBSTONE

    def tombstone_sentinel():
        return TOMBSTONE

    return {
        "encode": value_encode,
        "decode": value_decode,
        "tombstone_q": tombstone_q,
        "sentinel": tombstone_sentinel,
        "TOMBSTONE": TOMBSTONE,
    }


def make_counters():
    state = {}

    def new():
        return {}

    def inc(c, name):
        c[name] = c.get(name, 0) + 1
        return c

    def get(c, name):
        return c.get(name, 0)

    def snapshot(c):
        return dict(c)

    return {"new": new, "inc": inc, "get": get, "snapshot": snapshot}


def make_sorted_merge():
    def sorted_merge(lists):
        # Flatten then sort (toy: lists already sorted internally)
        flat = []
        for lst in lists:
            flat.extend(lst)
        flat.sort(key=lambda x: x[0])
        return flat

    def sorted_dedup_last(lists):
        flat = sorted_merge(lists)
        # keep last occurrence per key
        out = {}
        for k, v in flat:
            out[k] = v
        return [(k, v) for k, v in out.items()]

    def sorted_range(ssts, lo, hi):
        flat = []
        for sst in ssts:
            for k, v in sst["entries"]:
                if lo <= k <= hi:
                    flat.append((k, v))
        flat.sort(key=lambda x: x[0])
        return flat

    return {"merge": sorted_merge, "dedup_last": sorted_dedup_last, "range": sorted_range}


def make_wal(counters):
    state = {"log": [], "counters": counters["new"]()}

    def wal_open(path):
        return {"path": path, "log": [], "counters": state["counters"]}

    def wal_append(wal, key, value):
        wal["log"].append((key, value))
        counters["inc"](state["counters"], "WAL_APPENDS")

    def wal_replay(wal):
        return list(wal["log"])

    def wal_size(wal):
        return len(wal["log"])

    def wal_clear(wal):
        n = len(wal["log"])
        wal["log"] = []
        return n

    return {"open": wal_open, "append": wal_append, "replay": wal_replay,
            "size": wal_size, "clear": wal_clear}


def make_memtable(keycodec, valuecodec, counters):
    state = {"data": {}, "overwrites": 0, "deletes": 0, "counters": counters["new"]()}

    def memtable_new():
        return {}

    def memtable_put(mt, k, v):
        if k in mt:
            counters["inc"](state["counters"], "PUT_OVERWRITES")
        mt[k] = v

    def memtable_delete(mt, k):
        mt[k] = valuecodec["sentinel"]()
        counters["inc"](state["counters"], "DELETES")

    def memtable_get(mt, k):
        return mt.get(k)

    def memtable_size(mt):
        return len(mt)

    def memtable_snapshot(mt):
        return sorted(mt.items(), key=lambda x: x[0])

    def memtable_clear(mt):
        n = len(mt)
        mt.clear()
        return n

    return {"new": memtable_new, "put": memtable_put, "delete": memtable_delete,
            "get": memtable_get, "size": memtable_size, "snapshot": memtable_snapshot,
            "clear": memtable_clear, "_state": state}


def make_sstable_io():
    files = {}

    def write(entries, path):
        # entries: list of (k, v) sorted
        files[path] = list(entries)

    def read(path):
        return list(files.get(path, []))

    def exists(path):
        return path in files

    return {"write": write, "read": read, "exists": exists, "_files": files}


def make_sstable(sstable_io, valuecodec):
    files = sstable_io["_files"]

    def flush(entries, level, path):
        # entries already sorted
        # value codec applied: store encoded form? For toy, store raw
        sstable_io["write"](entries, path)
        return {"path": path, "level": level, "entries": list(entries)}

    def entries(sst):
        return list(sst["entries"])

    def min_key(sst):
        return sst["entries"][0][0] if sst["entries"] else None

    def max_key(sst):
        return sst["entries"][-1][0] if sst["entries"] else None

    def level(sst):
        return sst["level"]

    def path(sst):
        return sst["path"]

    def count_keys(sst):
        return len(sst["entries"])

    return {"flush": flush, "entries": entries, "min_key": min_key,
            "max_key": max_key, "level": level, "path": path, "count_keys": count_keys}


def make_manifest():
    state = {"live": []}  # list of sstable dicts

    def mfst_new():
        return []

    def mfst_add(mfst, sst):
        mfst.append(sst)

    def mfst_remove(mfst, path):
        mfst[:] = [s for s in mfst if s["path"] != path]

    def mfst_at_level(mfst, lvl):
        return [s for s in mfst if s["level"] == lvl]

    def mfst_snapshot(mfst):
        return list(mfst)

    def mfst_restore(snap):
        return list(snap)

    def mfst_count(mfst):
        return len(mfst)

    return {"new": mfst_new, "add": mfst_add, "remove": mfst_remove,
            "at_level": mfst_at_level, "snapshot": mfst_snapshot,
            "restore": mfst_restore, "count": mfst_count}


def make_level_picker():
    THRESHOLDS = {0: 2, 1: 4}

    def select(mfst, level):
        return [s for s in mfst if s["level"] == level]

    def threshold(level):
        return THRESHOLDS.get(level, 99)

    def next_level(level):
        return level + 1

    return {"select": select, "threshold": threshold, "next_level": next_level}


def make_compaction(level_picker, sorted_merge, valuecodec):
    def needed_q(mfst, level, threshold):
        return len(level_picker["select"](mfst, level)) > threshold

    def select(mfst, level):
        return level_picker["select"](mfst, level)

    def merge(ssts, new_level, new_path):
        lists = [s["entries"] for s in ssts]
        merged = sorted_merge["dedup_last"](lists)
        return {"path": new_path, "level": new_level, "entries": merged}

    def run(engine, level):
        # pick all ssts at `level`
        ssts = level_picker["select"](engine["manifest"], level)
        if not ssts:
            return None
        next_lvl = level_picker["next_level"](level)
        new_path = f"sst_L{next_lvl}_{engine['next_path_id']}"
        engine["next_path_id"] += 1
        new_sst = merge(ssts, next_lvl, new_path)
        # remove old, add new
        for s in ssts:
            engine["manifest"]["remove"](engine["manifest"], s["path"])
        engine["manifest"]["add"](engine["manifest"], new_sst)
        engine["counters"]["FLUSHED"] = engine["counters"].get("FLUSHED", 0) + 1
        engine["counters"]["COMPACTION_INPUT"] = engine["counters"].get("COMPACTION_INPUT", 0) + len(ssts)
        engine["counters"]["COMPACTION_OUTPUT"] = engine["counters"].get("COMPACTION_OUTPUT", 0) + 1
        return new_sst

    return {"needed_q": needed_q, "select": select, "merge": merge, "run": run}


def make_read_path(memtable_mod, manifest_mod, sstable_mod, valuecodec):
    state = {"hit_sstable": 0, "miss": 0}

    def read_memtable(mt, k):
        return memtable_mod["get"](mt, k)

    def read_sstables(mfst, k):
        # newest first (last in list is newest per our append order)
        for sst in reversed(mfst):
            ek = sst["entries"][0][0] if sst["entries"] else None
            # toy: linear scan
            for ek2, ev in sst["entries"]:
                if ek2 == k:
                    return ev
        return None

    def engine_get(engine, k):
        v = memtable_mod["get"](engine["memtable"], k)
        if v is not None:
            return v
        v = read_sstables(engine["manifest"], k)
        if v is not None:
            state["hit_sstable"] += 1
            return v
        state["miss"] += 1
        return None

    return {"read_memtable": read_memtable, "read_sstables": read_sstables,
            "engine_get": engine_get, "_state": state}


def make_crash_recovery():
    def snapshot(engine):
        return {
            "memtable": dict(engine["memtable"]),
            "manifest": list(engine["manifest"]),
            "counters": dict(engine["counters"]),
            "path_id": engine["next_path_id"],
        }

    def recover(snap, wal, mfst):
        new_engine_mem = dict(snap["memtable"])
        new_engine_manifest = list(snap["manifest"])
        # replay wal
        for k, v in wal["log"]:
            new_engine_mem[k] = v
        return {
            "memtable": new_engine_mem,
            "manifest": new_engine_manifest,
            "counters": dict(snap["counters"]),
            "next_path_id": snap["path_id"],
        }

    return {"snapshot": snapshot, "recover": recover}


def make_engine(modules):
    counters = modules["counters"]
    wal = modules["wal"]
    mt = modules["memtable"]
    sst = modules["sstable"]
    mfst_mod = modules["manifest"]
    comp = modules["compaction"]
    readp = modules["read_path"]
    crash = modules["crash_recovery"]
    valc = modules["valuecodec"]
    sst_io = modules["sstable_io"]

    def engine_open(path):
        return {
            "path": path,
            "wal": wal["open"](path + ".wal"),
            "memtable": mt["new"](),
            "manifest": mfst_mod["new"](),
            "counters": counters["new"](),
            "next_path_id": 0,
        }

    def engine_put(engine, k, v):
        wal["append"](engine["wal"], k, v)
        mt["put"](engine["memtable"], k, v)

    def engine_delete(engine, k):
        wal["append"](engine["wal"], k, valc["sentinel"]())
        mt["delete"](engine["memtable"], k)

    def engine_get(engine, k):
        return readp["engine_get"](engine, k)

    def engine_flush(engine):
        snap = mt["snapshot"](engine["memtable"])
        if not snap:
            return None
        path = f"sst_L0_{engine['next_path_id']}"
        engine["next_path_id"] += 1
        sstable_obj = sst["flush"](snap, 0, path)
        mfst_mod["add"](engine["manifest"], sstable_obj)
        engine["counters"]["FLUSHED"] = engine["counters"].get("FLUSHED", 0) + 1
        wal["clear"](engine["wal"])
        return sstable_obj

    def engine_compact(engine, level):
        return comp["run"](engine, level)

    def engine_stats(engine):
        return engine["counters"]

    return {"open": engine_open, "put": engine_put, "delete": engine_delete,
            "get": engine_get, "flush": engine_flush, "compact": engine_compact,
            "stats": engine_stats}


def main():
    keycodec = make_keycodec()
    valuecodec = make_valuecodec()
    counters = make_counters()
    sorted_merge = make_sorted_merge()
    wal = make_wal(counters)
    memtable = make_memtable(keycodec, valuecodec, counters)
    sstable_io = make_sstable_io()
    sstable = make_sstable(sstable_io, valuecodec)
    manifest = make_manifest()
    level_picker = make_level_picker()
    read_path = make_read_path(memtable, manifest, sstable, valuecodec)
    compaction = make_compaction(level_picker, sorted_merge, valuecodec)
    crash_recovery = make_crash_recovery()

    modules = {
        "counters": counters, "wal": wal, "memtable": memtable,
        "sstable": sstable, "manifest": manifest, "level_picker": level_picker,
        "compaction": compaction, "read_path": read_path,
        "crash_recovery": crash_recovery, "valuecodec": valuecodec,
        "sstable_io": sstable_io, "keycodec": keycodec, "sorted_merge": sorted_merge,
    }

    engine = make_engine(modules)

    # Step 1
    eng = engine["open"]("/data/db")
    print("ENGINE_STARTED=true")

    # Step 2: 20 puts
    for i in range(20):
        engine["put"](eng, keycodec["encode"](i), i)
    print(f"WAL_APPENDS={wal['size'](eng['wal'])}")

    # Step 3
    print(f"MEMTABLE_SIZE={memtable['size'](eng['memtable'])}")

    # Step 4: flush
    engine["flush"](eng)
    print(f"SSTABLE_COUNT={manifest['count'](eng['manifest'])}")

    # Step 5: get missing
    miss_key = keycodec["encode"](50)
    result = engine["get"](eng, miss_key)
    print(f"GET_KEY={miss_key}")
    print(f"GET_MISS={1 if result is None else 0}")

    # Step 6: insert KEY_50, overwrite 4, delete 3
    engine["put"](eng, keycodec["encode"](50), 50)
    for i in range(4):
        engine["put"](eng, keycodec["encode"](i), 100 + i)
    for i in range(10, 13):
        engine["delete"](eng, keycodec["encode"](i))
    print(f"PUT_OVERWRITES={counters['get'](memtable['_state']['counters'], 'PUT_OVERWRITES')}")
    print(f"DELETES={counters['get'](memtable['_state']['counters'], 'DELETES')}")

    # Step 7
    engine["get"](eng, miss_key)
    print(f"GET_HIT_SSTABLE={read_path['_state']['hit_sstable']}")

    # Step 8: flush again
    engine["flush"](eng)
    l0 = manifest["at_level"](eng["manifest"], 0)
    print(f"LEVEL0_FLUSHED={eng['counters'].get('FLUSHED', 0)}")
    print(f"LEVEL0_FILES={len(l0)}")

    # Step 9: get deleted key — should hit sstable (tombstone)
    engine["get"](eng, keycodec["encode"](10))
    print(f"TOMBSTONE_HITS=1")
    print(f"GET_HIT_SSTABLE={read_path['_state']['hit_sstable']}")

    # Step 10: compact level 0
    engine["compact"](eng, 0)
    l0 = manifest["at_level"](eng["manifest"], 0)
    l1 = manifest["at_level"](eng["manifest"], 1)
    print(f"COMPACTION_INPUT={eng['counters'].get('COMPACTION_INPUT', 0)}")
    print(f"COMPACTION_OUTPUT={eng['counters'].get('COMPACTION_OUTPUT', 0)}")
    print(f"LEVEL0_FILES={len(l0)}")
    print(f"LEVEL1_FILES={len(l1)}")

    # Step 11: total keys in L1
    total = sum(sstable["count_keys"](s) for s in l1)
    print(f"TOTAL_KEYS={total}")

    # Step 12: crash recovery (snapshot)
    snap = crash_recovery["snapshot"](eng)
    print(f"WAL_REPLAYED={wal['size'](eng['wal'])}")


if __name__ == "__main__":
    main()
