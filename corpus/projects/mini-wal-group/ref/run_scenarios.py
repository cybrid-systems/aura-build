import sys


# --- util.aura ---
def now_monotonic():
    return now_monotonic._t


def format_int(n):
    if isinstance(n, bool):
        return "1" if n else "0"
    return str(int(n))


# --- record.aura ---
def make_record(producer, payload, lsn):
    return {"producer": producer, "payload": payload, "lsn": lsn}


def record_lsn(r):
    return r["lsn"]


def record_producer(r):
    return r["producer"]


def record_payload(r):
    return r["payload"]


# --- batch.aura ---
def make_batch():
    return {"records": []}


def batch_add(b, r):
    b["records"].append(r)


def batch_size(b):
    return len(b["records"])


def batch_records(b):
    return b["records"]


def batch_min_lsn(b):
    recs = b["records"]
    return min(r["lsn"] for r in recs)


def batch_max_lsn(b):
    recs = b["records"]
    return max(r["lsn"] for r in recs)


# --- window.aura ---
def make_window(max_size, max_wait_ms):
    return {
        "buffer": [],
        "max_size": max_size,
        "max_wait_ms": max_wait_ms,
        "opened_at": 0,
    }


def window_try_add(w, r):
    if len(w["buffer"]) >= w["max_size"]:
        return False
    w["buffer"].append(r)
    return True


def window_should_flush(w, now):
    if not w["buffer"]:
        return False
    if len(w["buffer"]) >= w["max_size"]:
        return True
    if now - w["opened_at"] >= w["max_wait_ms"]:
        return True
    return False


def window_flush(w):
    recs = w["buffer"]
    b = make_batch()
    for r in recs:
        batch_add(b, r)
    return b


def window_rotate(w, now):
    w["buffer"] = []
    w["opened_at"] = now


def window_backpressure(w):
    # Returns the held records to retry in the new window.
    return w["buffer"]


# --- producer.aura ---
def make_producer(pid):
    return {"id": pid, "count": 0}


def producer_id(p):
    return p["id"]


def producer_count(p):
    return p["count"]


def producer_bump(p):
    p["count"] += 1


# --- fsync.aura ---
def make_fsync_counter():
    return {"value": 0, "notes": []}


def fsync_bump(c):
    c["value"] += 1


def fsync_value(c):
    return c["value"]


def fsync_note(c, n):
    c["notes"].append(n)


# --- backpressure.aura ---
def bp_counter():
    return {"value": 0}


def bp_inc(c):
    c["value"] += 1


def bp_value(c):
    return c["value"]


# --- commit.aura ---
def make_commit_log():
    return {
        "commits": [],
        "total_fsyncs": 0,
        "last_lsn": 0,
    }


def commit_append(log, batch, fsyncs):
    fsync_bump(fsyncs)
    log["total_fsyncs"] += 1
    if batch_size(batch) > 0:
        hi = batch_max_lsn(batch)
        if hi > log["last_lsn"]:
            log["last_lsn"] = hi
    log["commits"].append({
        "size": batch_size(batch),
        "fsyncs": fsync_value(fsyncs),
    })


def commit_count(log):
    return len(log["commits"])


def commit_total_fsyncs(log):
    return log["total_fsyncs"]


def commit_last_lsn(log):
    return log["last_lsn"]


def commit_snapshot(log):
    return {
        "commits": log["commits"][:],
        "total_fsyncs": log["total_fsyncs"],
        "last_lsn": log["last_lsn"],
        "count": len(log["commits"]),
    }


# --- coord.aura ---
def make_coord(max_batch, window_ms, producers, window, fsync, commit_log, bp):
    return {
        "max_batch": max_batch,
        "window_ms": window_ms,
        "producers": producers,
        "window": window,
        "fsync": fsync,
        "commit_log": commit_log,
        "bp": bp,
        "lsn": 0,
        "held": [],
        "stats": {"batch_sizes": [], "fsyncs": 0, "records": 0,
                  "backpressure": 0, "windows": 0},
    }


def coord_submit(c, r, now):
    c["stats"]["records"] += 1
    # Try adding to current window; if full, hold for next window.
    added = window_try_add(c["window"], r)
    if not added:
        # Backpressure: hold record and bump counter.
        bp_inc(c["bp"])
        c["stats"]["backpressure"] += 1
        c["held"].append(r)
    return added


def coord_do_flush(c, now):
    """Flush the current window if it should flush."""
    w = c["window"]
    if not window_should_flush(w, now):
        return
    batch = window_flush(w)
    size = batch_size(batch)
    if size > 0:
        commit_append(c["commit_log"], batch, c["fsync"])
        c["stats"]["batch_sizes"].append(size)
        c["stats"]["fsyncs"] += 1
        c["stats"]["windows"] += 1
    # Rotate window: start a new one, and move held records into it.
    window_rotate(w, now)
    held = c["held"]
    c["held"] = []
    for hr in held:
        # If new window has room, add; else drop to held again.
        ok = window_try_add(w, hr)
        if not ok:
            bp_inc(c["bp"])
            c["stats"]["backpressure"] += 1
            c["held"].append(hr)


def coord_tick(c, now):
    coord_do_flush(c, now)


def coord_stats(c):
    return {
        "records": c["stats"]["records"],
        "batches": len(c["stats"]["batch_sizes"]),
        "batch_sizes": c["stats"]["batch_sizes"][:],
        "fsyncs": c["stats"]["fsyncs"],
        "backpressure": c["stats"]["backpressure"],
        "windows": c["stats"]["windows"],
        "lsn": c["lsn"],
    }


# --- stats.aura ---
def make_stats():
    return {"batch_sizes": [], "records": 0}


def stats_record(s):
    s["records"] += 1


def stats_batch(s, size):
    s["batch_sizes"].append(size)


def stats_finalize(s, producers, windows, backpressure_waits):
    recs_per_prod = [producer_count(p) for p in producers]
    total = sum(s["batch_sizes"])
    batches = len(s["batch_sizes"])
    avg = (total // batches) if batches > 0 else 0
    mx = max(s["batch_sizes"]) if s["batch_sizes"] else 0
    return {
        "records_per_producer": recs_per_prod,
        "batches": batches,
        "total_records_in_batches": total,
        "avg_batch": avg,
        "max_batch": mx,
        "backpressure_waits": backpressure_waits,
        "windows": windows,
    }


# --- main.aura scenario ---
def main():
    # Reset monotonic clock.
    now_monotonic._t = 0

    # 1. Build 3 producers.
    producers = [make_producer(0), make_producer(1), make_producer(2)]

    # 2. Create a window: max-size=10, max-wait-ms=5.
    window = make_window(10, 5)

    # 3. Create commit-log, fsync-counter, bp-counter.
    commit_log = make_commit_log()
    fsync = make_fsync_counter()
    bp = bp_counter()

    # 4. Build coord.
    coord = make_coord(10, 5, producers, window, fsync, commit_log, bp)
    # Open the first window.
    window_rotate(coord["window"], now_monotonic())

    # 5. Submit 42 records, interleaved across producers.
    # Pattern: producer indices 0..2 cycled, producer bumps count per submit.
    total_records = 42
    schedule = []
    for i in range(total_records):
        pid = i % 3
        schedule.append(pid)

    lsn = 0
    # Make a local increasing clock independent of any external imports.
    clock = {"t": 0}

    def tick_now():
        clock["t"] += 1
        now_monotonic._t = clock["t"]
        return clock["t"]

    # Open the window at t=0 (already rotated above with now=0).
    coord["window"]["opened_at"] = 0

    submitted = 0
    i = 0
    while submitted < total_records:
        pid = schedule[i]
        lsn += 1
        rec = make_record(pid, "p" + format_int(pid) + "-" + format_int(lsn), lsn)
        producer_bump(producers[pid])
        coord["lsn"] = lsn
        # Submit at current now.
        t = tick_now()
        coord_submit(coord, rec, t)
        # Tick to drive flushes.
        coord_tick(coord, t)
        submitted += 1
        i += 1

    # 7. After last submit, run ticks until the trailing window flushes.
    # Keep ticking; window will flush when it reaches max-wait-ms=5 or max-size=10.
    safety = 0
    while coord["window"]["buffer"]:
        t = tick_now()
        coord_tick(coord, t)
        safety += 1
        if safety > 1000:
            break

    # 8. Compute summary stats.
    s = make_stats()
    for _ in range(coord["stats"]["records"]):
        stats_record(s)
    for bs in coord["stats"]["batch_sizes"]:
        stats_batch(s, bs)
    summary = stats_finalize(
        s,
        producers,
        commit_count(commit_log),
        bp_value(bp),
    )

    # 9. Print the 11 KEY=value lines in order.
    out = []
    out.append("WAL_PRODUCERS=" + format_int(len(producers)))
    out.append("WAL_RECORDS=" + format_int(coord["stats"]["records"]))
    out.append("WAL_BATCHES=" + format_int(commit_count(commit_log)))
    out.append("WAL_FSYNCS=" + format_int(fsync_value(fsync)))
    out.append("WAL_AVG_BATCH=" + format_int(summary["avg_batch"]))
    out.append("WAL_MAX_BATCH=" + format_int(summary["max_batch"]))
    out.append("WAL_BACKPRESSURE_WAITS=" + format_int(bp_value(bp)))
    out.append("WAL_WINDOWS=" + format_int(commit_count(commit_log)))
    out.append("WAL_LSN=" + format_int(coord["lsn"]))
    out.append("WAL_COMMIT_LSN=" + format_int(commit_last_lsn(commit_log)))

    sys.stdout.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
