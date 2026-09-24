# run_scenarios.py
import copy

# ---------- hash ----------
def hash_fold(n):
    # FNV-1a 32-bit
    h = 2166136261 & 0xFFFFFFFF
    for i in range(32):
        h ^= (n >> (i * 8)) & 0xFF
        h = (h * 16777619) & 0xFFFFFFFF
    return h

# ---------- event ----------
def event_make(user_id, delta, ts):
    return ("event", user_id, delta, ts)

def event_is(x):
    return isinstance(x, tuple) and len(x) == 4 and x[0] == "event"

def event_user_id(e):
    return e[1]

def event_delta(e):
    return e[2]

def event_ts(e):
    return e[3]

# ---------- tiers ----------
def tier_make(kind, cap=None):
    return {"kind": kind, "data": {}, "cap": cap, "touches": {}}

def tier_step(t, k, delta):
    t["data"][k] = t["data"].get(k, 0) + delta
    t["touches"][k] = t["touches"].get(k, 0) + 1

def tier_get(t, k):
    return t["data"].get(k, 0)

def tier_keys(t):
    return sorted(t["data"].keys())

def tier_size(t):
    return len(t["data"])

def tier_promote(t, k):
    touches = t["touches"].get(k, 0)
    if t["kind"] == "hashmap" and touches >= 3:
        return "sorted"
    if t["kind"] == "sorted" and len(t["data"]) >= (t["cap"] or 4):
        return "overflow"
    return None

# ---------- tier factories ----------
def hashmap_tier_new():
    return tier_make("hashmap")

def sorted_tier_new():
    return tier_make("sorted", cap=4)

def overflow_tier_new(cap):
    return tier_make("overflow", cap=cap)

# ---------- aggregator ----------
def agg_make():
    return {"sum": {}, "count": {}}

def agg_step(agg, k, delta, ts):
    agg["sum"][k] = agg["sum"].get(k, 0) + delta
    if delta >= 0:
        agg["count"][k] = agg["count"].get(k, 0) + 1
    else:
        agg["count"][k] = max(0, agg["count"].get(k, 0) - 1)

def agg_final(agg, k):
    return agg["sum"].get(k, 0)

# ---------- watermark ----------
def wm_advance(wm, ts):
    return max(wm, ts)

def wm_is_late(wm, ts):
    return ts < wm

def wm_current(wm):
    return wm

# ---------- checkpoint ----------
def ckpt_snapshot(state):
    return copy.deepcopy(state)

def ckpt_restore(snap):
    return copy.deepcopy(snap)

def ckpt_hash(state):
    # fold a dict to int then hash
    acc = 0
    for k in sorted(state.keys()):
        v = state[k]
        if isinstance(v, dict):
            v = ckpt_hash(v)
        acc = (acc * 31 + hash(v)) & 0xFFFFFFFFFFFFFFFF
    return hash_fold(acc)

# ---------- metrics ----------
def metrics_record(m, tier, kind, key):
    m.setdefault("events", 0)
    m["events"] += 1

def metrics_snapshot(m):
    return dict(m)

# ---------- demo events ----------
def demo_events_build():
    # deterministic stream
    return [
        event_make("u1", 10, 1),
        event_make("u2", 5, 2),
        event_make("u1", 3, 3),
        event_make("u3", 7, 4),
        event_make("u1", -2, 5),
        event_make("u2", 4, 6),
        event_make("u3", -1, 7),
        event_make("u1", 8, 8),
        event_make("u4", 2, 9),
        event_make("u2", -3, 10),
    ]

# ---------- engine ----------
def engine_new():
    return {
        "name": "mini-stream-agg",
        "agg": agg_make(),
        "wm": 0,
        "tiers": {
            "hashmap": hashmap_tier_new(),
            "sorted": sorted_tier_new(),
            "overflow": overflow_tier_new(cap=3),
        },
        "accepts": 0,
        "retracts": 0,
        "promotions": 0,
        "demotions": 0,
        "checkpoints": [],
        "events_processed": 0,
    }

def _place_key(eng, k, delta):
    # find which tier has the key
    for tier_name, t in eng["tiers"].items():
        if k in t["data"]:
            tier_step(t, k, delta)
            return tier_name
    # not found; place in hashmap
    tier_step(eng["tiers"]["hashmap"], k, delta)
    return "hashmap"

def _maybe_promote(eng):
    # check hashmap -> sorted
    hm = eng["tiers"]["hashmap"]
    to_promote = []
    for k in list(hm["data"].keys()):
        if tier_promote(hm, k) == "sorted":
            to_promote.append(k)
    for k in to_promote:
        val = hm["data"].pop(k)
        hm["touches"].pop(k, None)
        eng["tiers"]["sorted"]["data"][k] = eng["tiers"]["sorted"]["data"].get(k, 0) + val
        eng["promotions"] += 1
    # check sorted -> overflow
    st = eng["tiers"]["sorted"]
    to_overflow = []
    if len(st["data"]) > st["cap"]:
        for k in sorted(st["data"].keys()):
            if len(eng["tiers"]["overflow"]["data"]) >= eng["tiers"]["overflow"]["cap"]:
                break
            if tier_promote(st, k) == "overflow":
                to_overflow.append(k)
    for k in to_overflow:
        val = st["data"].pop(k)
        eng["tiers"]["overflow"]["data"][k] = eng["tiers"]["overflow"]["data"].get(k, 0) + val
        eng["promotions"] += 1

def engine_step(eng, event):
    e = event
    k = event_user_id(e)
    d = event_delta(e)
    ts = event_ts(e)
    eng["events_processed"] += 1
    if d < 0 or wm_is_late(eng["wm"], ts):
        eng["retracts"] += 1
    else:
        eng["accepts"] += 1
    eng["wm"] = wm_advance(eng["wm"], ts)
    agg_step(eng["agg"], k, d, ts)
    _place_key(eng, k, d)
    _maybe_promote(eng)
    if eng["events_processed"] % 5 == 0:
        engine_checkpoint(eng)

def engine_flush(eng):
    pass

def engine_stats(eng):
    return {
        "events_processed": eng["events_processed"],
        "accepts": eng["accepts"],
        "retracts": eng["retracts"],
        "final_user_sum": eng["agg"]["sum"],
        "final_user_count": eng["agg"]["count"],
        "final_distinct_users": len(eng["agg"]["sum"]),
    }

def engine_tier_counts(eng):
    return {
        "hot_tier_keys": tier_size(eng["tiers"]["hashmap"]),
        "sorted_tier_keys": tier_size(eng["tiers"]["sorted"]),
        "overflow_tier_keys": tier_size(eng["tiers"]["overflow"]),
    }

def engine_promotions(eng):
    return eng["promotions"]

def engine_demotions(eng):
    return eng["demotions"]

def engine_checkpoint(eng):
    snap = ckpt_snapshot(eng["agg"])
    eng["checkpoints"].append(snap)

# ---------- recovery ----------
def recovery_replay(events, checkpoints):
    # replay into a fresh engine and compare checkpoints
    eng2 = engine_new()
    for i, e in enumerate(events):
        engine_step(eng2, e)
    # match if checkpoint count and hashes match
    if len(checkpoints) != len(eng2["checkpoints"]):
        return eng2["agg"], False
    for a, b in zip(checkpoints, eng2["checkpoints"]):
        if ckpt_hash(a) != ckpt_hash(b):
            return eng2["agg"], False
    return eng2["agg"], True

# ---------- main ----------
if __name__ == "__main__":
    events = demo_events_build()
    eng = engine_new()
    for e in events:
        engine_step(eng, e)
    engine_flush(eng)
    repl_agg, match = recovery_replay(events, eng["checkpoints"])
    stats = engine_stats(eng)
    tiers = engine_tier_counts(eng)
    end_hash_hex = format(hash_fold(sum(eng["agg"]["sum"].values()) + len(eng["agg"]["sum"]) * 7), "08x")

    print(f"ENGINE_NAME={eng['name']}")
    print(f"EVENTS_PROCESSED={stats['events_processed']}")
    print(f"ACCEPTS={stats['accepts']}")
    print(f"RETractS={stats['retracts']}")
    u1_sum = eng["agg"]["sum"].get("u1", 0)
    u1_cnt = eng["agg"]["count"].get("u1", 0)
    print(f"FINAL_USER_SUM={u1_sum}")
    print(f"FINAL_USER_COUNT={u1_cnt}")
    print(f"FINAL_DISTINCT_USERS={stats['final_distinct_users']}")
    print(f"HOT_TIER_KEYS={tiers['hot_tier_keys']}")
    print(f"SORTED_TIER_KEYS={tiers['sorted_tier_keys']}")
    print(f"OVERFLOW_TIER_KEYS={tiers['overflow_tier_keys']}")
    print(f"PROMOTIONS={eng['promotions']}")
    print(f"DEMOTIONS={eng['demotions']}")
    print(f"CHECKPOINT_EPOCHS={len(eng['checkpoints'])}")
    print(f"REPLAY_MATCH={'#t' if match else '#f'}")
    print(f"END_STATE_HASH={end_hash_hex}")
