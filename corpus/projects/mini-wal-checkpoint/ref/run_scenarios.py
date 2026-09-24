# Mini WAL Checkpoint Engine - Python reference
import random

# --- constants module ---
MIN_PAGE_ID = 1
MAX_PAGE_ID = 64
LSN_START = 1000
CHECKPOINT_INTERVAL_CONST = 8
MAX_PAGES_PER_FUZZY = 16

# --- lsn module ---
def make_lsn(n):
    return int(n)

def lsn_advance(lsn, delta):
    return lsn + delta

def lsn_diff(a, b):
    return a - b

def lsn_le(a, b):
    return a <= b

# --- page-table module ---
def make_page_table():
    return {"dirty": set(), "reset_count": 0}

def page_dirty(pt, pid):
    pt["dirty"].add(pid)

def page_dirty_q(pt, pid):
    return pid in pt["dirty"]

def dirty_pages(pt):
    return frozenset(pt["dirty"])

def dirty_page_count(pt):
    return len(pt["dirty"])

def reset_dirty_bits(pt):
    n = len(pt["dirty"])
    pt["dirty"] = set()
    pt["reset_count"] += 1
    return n

def page_table_size(pt):
    return len(pt["dirty"])

# --- redo-record module ---
RECORD_OVERHEAD = 16
def make_redo(lsn, pid, payload=64):
    return {"lsn": lsn, "pid": pid, "size": payload + RECORD_OVERHEAD}

def redo_page_id(r):
    return r["pid"]

def redo_lsn(r):
    return r["lsn"]

def redo_size(r):
    return r["size"]

# --- redo-log module ---
def make_redo_log():
    return {"records": [], "bytes": 0, "bytes_since_last": 0}

def redo_log_append(log, rec):
    log["records"].append(rec)
    log["bytes"] += rec["size"]
    log["bytes_since_last"] += rec["size"]
    return log

def redo_log_length(log):
    return len(log["records"])

def redo_log_bytes(log):
    return log["bytes"]

def redo_log_bytes_since(log):
    return log["bytes_since_last"]

def reset_bytes_since(log):
    n = log["bytes_since_last"]
    log["bytes_since_last"] = 0
    return n

# --- checkpoint module ---
def make_checkpoint(start_lsn, end_lsn, pages):
    return {"start": start_lsn, "end": end_lsn, "pages": frozenset(pages)}

def checkpoint_start_lsn(cp):
    return cp["start"]

def checkpoint_end_lsn(cp):
    return cp["end"]

def checkpoint_dirty_pages(cp):
    return cp["pages"]

# --- fuzzy-collector module ---
def make_fuzzy_collector():
    return {"pages": set(), "cap": MAX_PAGES_PER_FUZZY, "count": 0}

def fuzzy_collect(fc, pages):
    for p in pages:
        if len(fc["pages"]) < fc["cap"]:
            fc["pages"].add(p)
    fc["count"] = len(fc["pages"])
    return fc

def fuzzy_reset(fc):
    fc["pages"] = set()
    fc["count"] = 0

def fuzzy_count(fc):
    return fc["count"]

# --- stats module ---
def make_stats():
    return {"counters": {}}

def stats_inc(st, key, n=1):
    st["counters"][key] = st["counters"].get(key, 0) + n

def stats_get(st, key):
    return st["counters"].get(key, 0)

def stats_snapshot(st):
    return dict(st["counters"])

# --- config module ---
def default_config():
    return {"checkpoint-interval": CHECKPOINT_INTERVAL_CONST, "fuzzy-cap": MAX_PAGES_PER_FUZZY}

def config_checkpoint_interval(cfg):
    return cfg["checkpoint-interval"]

def config_fuzzy_cap(cfg):
    return cfg["fuzzy-cap"]

# --- checkpoint-engine module ---
def make_engine(config):
    pt = make_page_table()
    rl = make_redo_log()
    fc = make_fuzzy_collector()
    st = make_stats()
    fc["cap"] = config_fuzzy_cap(config)
    return {
        "config": config,
        "pt": pt,
        "rl": rl,
        "fc": fc,
        "st": st,
        "current_lsn": LSN_START,
        "records_since_checkpoint": 0,
        "checkpoint_history": [],
        "dirty_before": set(),
    }

def engine_emit_redo(engine, pid):
    lsn = engine["current_lsn"]
    rec = make_redo(lsn, pid)
    redo_log_append(engine["rl"], rec)
    page_dirty(engine["pt"], pid)
    engine["dirty_before"].add(pid)
    engine["current_lsn"] = lsn_advance(lsn, 1)
    engine["records_since_checkpoint"] += 1
    stats_inc(engine["st"], "REDO_RECORDS")
    stats_inc(engine["st"], "PAGES_DIRTIED")
    stats_inc(engine["st"], "REDO_BYTES", rec["size"])
    return rec

def engine_should_checkpoint(engine):
    interval = config_checkpoint_interval(engine["config"])
    return engine["records_since_checkpoint"] >= interval

def engine_emit_checkpoint(engine):
    # Capture dirty pages for fuzzy collection
    pages = list(dirty_pages(engine["pt"]))
    fuzzy_collect(engine["fc"], pages)
    fuzzy_pages_now = fuzzy_count(engine["fc"])
    # Make checkpoint anchored at current_lsn - records_since_checkpoint
    start_lsn = engine["current_lsn"] - engine["records_since_checkpoint"]
    end_lsn = engine["current_lsn"] - 1
    cp = make_checkpoint(start_lsn, end_lsn, pages)
    engine["checkpoint_history"].append(cp)
    # Reset dirty bits
    reset_dirty_bits(engine["pt"])
    stats_inc(engine["st"], "CHECKPOINTS_EMITTED")
    stats_inc(engine["st"], "CHECKPOINT_COUNT")
    stats_inc(engine["st"], "DIRTY_BIT_RESET")
    # Reset fuzzy collector and record counters
    engine["records_since_checkpoint"] = 0
    reset_bytes_since(engine["rl"])
    # Track last checkpoint LSN
    stats_set(engine["st"], "LAST_CHECKPOINT_LSN", end_lsn)
    return cp

def stats_set(st, key, val):
    st["counters"][key] = val

def engine_stats(engine):
    return stats_snapshot(engine["st"])

def engine_replay_from_lsn(engine):
    if not engine["checkpoint_history"]:
        return LSN_START
    last = engine["checkpoint_history"][-1]
    return checkpoint_end_lsn(last) + 1

def engine_max_replay_length(engine):
    return engine["records_since_checkpoint"]

# --- recovery module ---
def recovery_replay_from(engine):
    return engine_replay_from_lsn(engine)

def recovery_scan_window(engine):
    # Maximum bytes we'd need to scan from last checkpoint LSN to current tip
    if not engine["checkpoint_history"]:
        return engine["rl"]["bytes"]
    last = engine["checkpoint_history"][-1]
    start = checkpoint_end_lsn(last) + 1
    total = 0
    for r in engine["rl"]["records"]:
        if redo_lsn(r) >= start:
            total += redo_size(r)
    return total

def recovery_reset_dirty_count(engine):
    return engine["pt"]["reset_count"]

# --- report module ---
def fmt(key, value):
    return f"{key}={value}"

# --- main scenario ---
def main():
    random.seed(20240115)
    cfg = default_config()
    engine = make_engine(cfg)

    N = 32
    interval = config_checkpoint_interval(cfg)

    for i in range(N):
        pid = random.randint(MIN_PAGE_ID, MAX_PAGE_ID)
        engine_emit_redo(engine, pid)
        if engine_should_checkpoint(engine):
            engine_emit_checkpoint(engine)

    # Gather metrics
    lsn = engine["current_lsn"]
    pages_dirtied = stats_get(engine["st"], "PAGES_DIRTIED")
    checkpoint_count = stats_get(engine["st"], "CHECKPOINT_COUNT")
    last_checkpoint_lsn = stats_get(engine["st"], "LAST_CHECKPOINT_LSN")
    if last_checkpoint_lsn == 0:
        last_checkpoint_lsn = LSN_START
    redo_records = stats_get(engine["st"], "REDO_RECORDS")
    fuzzy_pages = fuzzy_count(engine["fc"])
    replay_from_lsn = recovery_replay_from(engine)
    max_replay_length = recovery_scan_window(engine)
    checkpoint_interval = config_checkpoint_interval(cfg)
    dirty_bit_reset = recovery_reset_dirty_count(engine)
    redo_bytes = stats_get(engine["st"], "REDO_BYTES")
    checkpoints_emitted = stats_get(engine["st"], "CHECKPOINTS_EMITTED")

    # Emit the 12 KEY=value lines (LSN first)
    print(fmt("LSN", lsn))
    print(fmt("PAGES_DIRTIED", pages_dirtied))
    print(fmt("CHECKPOINT_COUNT", checkpoint_count))
    print(fmt("LAST_CHECKPOINT_LSN", last_checkpoint_lsn))
    print(fmt("REDO_RECORDS", redo_records))
    print(fmt("FUZZY_PAGES", fuzzy_pages))
    print(fmt("REPLAY_FROM_LSN", replay_from_lsn))
    print(fmt("MAX_REPLAY_LENGTH", max_replay_length))
    print(fmt("CHECKPOINT_INTERVAL", checkpoint_interval))
    print(fmt("DIRTY_BIT_RESET", dirty_bit_reset))
    print(fmt("REDO_BYTES", redo_bytes))
    print(fmt("CHECKPOINTS_EMITTED", checkpoints_emitted))

if __name__ == "__main__":
    main()
