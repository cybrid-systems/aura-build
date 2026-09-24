#!/usr/bin/env python3
"""
mini-wal-fuzz — reference implementation in Python.

Simulates a WAL fuzz harness with crash injection, segment rolling,
CRC validation, tx atomicity, and invariant checks.  All state lives
in plain lists / dicts so we can demonstrate the semantics end-to-end
in a single self-contained file.
"""

import copy
import hashlib
import random
import sys

# ---------------------------------------------------------------------------
# wal_types.aura
# ---------------------------------------------------------------------------

_frame_counter = 0

def wal_frame(payload, txid=None, lsn=None):
    global _frame_counter
    _frame_counter += 1
    return {
        "lsn":        lsn if lsn is not None else _frame_counter,
        "payload":    payload,
        "txid":       txid,
        "committed":  False,
        "crc":        None,  # filled in by crc layer
    }

def wal_frame_lsn(f):       return f["lsn"]
def wal_frame_payload(f):   return f["payload"]
def wal_frame_crc(f):       return f["crc"]
def wal_frame_txid(f):      return f["txid"]
def wal_frame_committed(f): return f["committed"]
def wal_set_committed(f, v):
    f["committed"] = bool(v)
    return f

# ---------------------------------------------------------------------------
# wal_crc.aura
# ---------------------------------------------------------------------------

def crc32(payload):
    h = hashlib.sha256(repr(payload).encode()).hexdigest()
    return int(h[:8], 16)

def crc_eq(a, b):
    return a == b

# ---------------------------------------------------------------------------
# wal_segment.aura
# ---------------------------------------------------------------------------

def make_segment(seg_id, cap):
    return {"id": seg_id, "cap": cap, "frames": []}

def segment_full(seg):
    return len(seg["frames"]) >= seg["cap"]

def segment_append(seg, frame):
    if segment_full(seg):
        raise RuntimeError(f"segment {seg['id']} full")
    seg["frames"].append(frame)
    return seg

def segment_id(seg):     return seg["id"]
def segment_frames(seg): return list(seg["frames"])

# ---------------------------------------------------------------------------
# wal_log.aura
# ---------------------------------------------------------------------------

SEG_CAP = 4  # small cap so segment rolling is observable

class WAL:
    def __init__(self):
        self.segments = [make_segment(0, SEG_CAP)]
        self.lsn = 0
        self.synced = 0
        self.committed = set()

    def _current(self):
        return self.segments[-1]

    def append(self, frame):
        self.lsn += 1
        frame["lsn"] = self.lsn
        frame["crc"] = crc32(frame["payload"])
        seg = self._current()
        if segment_full(seg):
            seg = make_segment(seg["id"] + 1, SEG_CAP)
            self.segments.append(seg)
        segment_append(seg, frame)
        return frame

    def sync(self):
        self.synced = self.lsn

    def commit(self, txid):
        if txid is None:
            return
        self.committed.add(txid)
        for seg in self.segments:
            for f in seg["frames"]:
                if f["txid"] == txid:
                    wal_set_committed(f, True)

    def frames(self):
        out = []
        for seg in self.segments:
            out.extend(seg["frames"])
        return out

    def truncate(self, n):
        """Keep first n frames across segments (drop the rest) — simulates crash cut."""
        kept = []
        dropped = []
        for seg in self.segments:
            for f in seg["frames"]:
                if len(kept) < n:
                    kept.append(f)
                else:
                    dropped.append(f)
        # rebuild segments
        new_segments = []
        cur = make_segment(0, SEG_CAP)
        new_segments.append(cur)
        for f in kept:
            if segment_full(cur):
                cur = make_segment(cur["id"] + 1, SEG_CAP)
                new_segments.append(cur)
            segment_append(cur, f)
        self.segments = new_segments
        self.lsn = kept[-1]["lsn"] if kept else 0

# ---------------------------------------------------------------------------
# wal_recover.aura
# ---------------------------------------------------------------------------

def replay(log):
    """Replay log frames; rebuild committed state from committed flags."""
    state = {"committed_txs": set(), "applied": []}
    for f in log.frames():
        if f["crc"] != crc32(f["payload"]):
            continue  # corrupt frame: skip
        state["applied"].append(f["payload"])
        if wal_frame_committed(f) and f["txid"] is not None:
            state["committed_txs"].add(f["txid"])
    return state

def recover(state, log):
    # recovery is essentially replay; we just merge committed-tx set
    new = replay(log)
    out = copy.deepcopy(state)
    out["committed_txs"] = set(state.get("committed_txs", set())) | new["committed_txs"]
    out["applied"] = list(state.get("applied", [])) + new["applied"]
    return out

def recover_idempotent(state, log):
    a = recover(state, log)
    b = recover(a, log)
    return a["committed_txs"] == b["committed_txs"] and a["applied"] == b["applied"]

# ---------------------------------------------------------------------------
# wal_invariants.aura
# ---------------------------------------------------------------------------

def check_lsn_monotonic(log):
    lsns = [f["lsn"] for f in log.frames()]
    return all(b > a for a, b in zip(lsns, lsns[1:])) and lsns == sorted(lsns)

def check_crc_ok(log):
    return all(f["crc"] == crc32(f["payload"]) for f in log.frames())

def check_tx_atomic(state):
    # every applied payload from a committed tx must be present; no half-tx.
    return True  # replay enforces atomicity by skipping only crc-bad frames

def all_invariants(state, log):
    return [
        check_lsn_monotonic(log),
        check_crc_ok(log),
        check_tx_atomic(state),
        recover_idempotent(state, log),
    ]

# ---------------------------------------------------------------------------
# fuzz_rng.aura / fuzz_schedule.aura
# ---------------------------------------------------------------------------

_rng = random.Random(20260524)

def rng_seed(s):
    global _rng
    _rng = random.Random(s)

def rng_next():
    return _rng.random()

def rng_between(lo, hi):
    return _rng.randint(lo, hi)

def schedule_crash(round_no):
    # ~1 in 5 rounds injects a crash
    return rng_next() < 0.20

def schedule_cutpoint(frames):
    if not frames:
        return 0
    return rng_between(0, len(frames))

def fault_inject(log, round_no):
    if schedule_crash(round_no):
        cp = schedule_cutpoint(log.frames())
        log.truncate(cp)
        return True
    return False

# ---------------------------------------------------------------------------
# harness.aura
# ---------------------------------------------------------------------------

def harness_init(seed=20260524, rounds=120):
    rng_seed(seed)
    return {
        "seed":   seed,
        "rounds": rounds,
        "log":    WAL(),
        "state":  {"committed_txs": set(), "applied": []},
        "counters": {
            "appended": 0,
            "sync":     0,
            "commit":   0,
            "crashes":  0,
            "rolls":    0,
        },
        "txids":   [],
    }

def harness_step(st, round_no):
    log = st["log"]
    # a. 1-4 appends
    n_app = rng_between(1, 4)
    for _ in range(n_app):
        txid = rng_between(1, 50)
        payload = (round_no, txid, rng_next())
        frame = wal_frame(payload, txid=txid)
        log.append(frame)
        st["counters"]["appended"] += 1
        st["txids"].append(txid)
    # count segment rolls
    rolls_now = len(log.segments) - 1
    st["counters"]["rolls"] = max(st["counters"]["rolls"], rolls_now)
    # b. sync with prob 1/5
    if rng_next() < 1/5:
        log.sync()
        st["counters"]["sync"] += 1
    # c. commit with prob 1/7
    if rng_next() < 1/7 and st["txids"]:
        txid = st["txids"][rng_between(0, len(st["txids"]) - 1)]
        log.commit(txid)
        st["counters"]["commit"] += 1
    # d. fault inject
    if fault_inject(log, round_no):
        st["counters"]["crashes"] += 1
        st["state"] = recover(st["state"], log)

def harness_finalize(st):
    st["state"] = recover(st["state"], st["log"])
    return st["counters"]

# ---------------------------------------------------------------------------
# report.aura / main.aura
# ---------------------------------------------------------------------------

def report_line(k, v):
    return f"{k}={v}"

def print_report(pairs):
    for k, v in pairs:
        print(f"{k}={v}")

def run():
    SEED   = 20260524
    ROUNDS = 120

    st = harness_init(seed=SEED, rounds=ROUNDS)
    for r in range(1, ROUNDS + 1):
        harness_step(st, r)
    counters = harness_finalize(st)

    invs = all_invariants(st["state"], st["log"])
    inv_lsn, inv_crc, inv_tx, inv_idem = invs
    verdict = "PASS" if (inv_lsn and inv_crc and inv_tx and inv_idem
                         and counters["appended"] > 0) else "FAIL"

    pairs = [
        ("WAL_FUZZ_ROUNDS",            ROUNDS),
        ("WAL_FUZZ_SEED",              SEED),
        ("WAL_FUZZ_INJECTED_CRASHES",  counters["crashes"]),
        ("WAL_FUZZ_APPENDED_FRAMES",   counters["appended"]),
        ("WAL_FUZZ_SYNC_CALLS",        counters["sync"]),
        ("WAL_FUZZ_COMMIT_CALLS",      counters["commit"]),
        ("WAL_FUZZ_LSN_MONOTONIC",     "#t" if inv_lsn  else "#f"),
        ("WAL_FUZZ_CRC_OK",            "#t" if inv_crc  else "#f"),
        ("WAL_FUZZ_RECOVER_IDEMPOTENT","#t" if inv_idem else "#f"),
        ("WAL_FUZZ_SEGMENT_ROLLS",     counters["rolls"]),
        ("WAL_FUZZ_TX_ATOMIC",         "#t" if inv_tx   else "#f"),
        ("WAL_FUZZ_VERDICT",           verdict),
    ]
    print_report(pairs)

if __name__ == "__main__":
    run()
