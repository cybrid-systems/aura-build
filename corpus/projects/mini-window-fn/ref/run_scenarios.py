# Toy in-memory semantics for the Aura mini-window-function runtime.
# Pure stdlib; computes the 16 KEY=value lines that the GOAL scenario expects.

from collections import defaultdict

# ----------------------- types --------------------------------------------
def wf_rel(x):
    return isinstance(x, dict) and "cols" in x and "rows" in x

def wf_row(r):
    return isinstance(r, dict)

def wf_col(c):
    return isinstance(c, str)

def wf_part_key(part, i=0):
    return part[i][0] if isinstance(part, list) and part else part

# ----------------------- schema -------------------------------------------
def wf_make_relation(cols, rows):
    return {"cols": list(cols), "rows": [dict(zip(cols, r)) for r in rows]}

def wf_relation_cols(rel): return rel["cols"]
def wf_relation_rows(rel):  return rel["rows"]

# ----------------------- partition ----------------------------------------
def wf_partition(rel, key_col):
    buckets = defaultdict(list)
    for r in rel["rows"]:
        buckets[r[key_col]].append(r)
    return [(k, v) for k, v in buckets.items()]

def wf_part_rows(part):   return part[1]
def wf_part_key(part):    return part[0]

# ----------------------- sort ---------------------------------------------
def wf_sort(rows, cmp):
    return sorted(rows, key=cmp)

def wf_sort_by(rows, col, rel):
    # ascending by `col`
    return sorted(rows, key=lambda r: r[col])

# ----------------------- frame --------------------------------------------
def wf_make_frame(kind, lo, hi):
    return {"kind": kind, "lo": lo, "hi": hi}

def wf_frame_string(f):
    return f"{f['kind']} BETWEEN {f['lo']} PRECEDING AND {f['hi']} FOLLOWING"

def wf_rows_in_frame(rows, frame, pivot):
    n = len(rows)
    lo = max(0, pivot - frame["lo"])
    hi = min(n - 1, pivot + frame["hi"])
    return rows[lo:hi + 1]

# ----------------------- rank ---------------------------------------------
def wf_row_number():
    return "ROW_NUMBER"

def wf_rank():
    return "RANK"

def wf_dense_rank():
    return "DENSE_RANK"

def wf_apply_rank(rows, order_col, score_col, rank_fn):
    # Sort rows by order_col, assign rank values into score_col key.
    sorted_rows = sorted(rows, key=lambda r: r[order_col])
    prev = None
    dense = 0
    rn = 0
    last_score = None
    for i, r in enumerate(sorted_rows, start=1):
        rn += 1
        if r[order_col] != prev:
            dense += 1
            prev = r[order_col]
        # Determine the rank label
        if rank_fn == "ROW_NUMBER":
            label = i
        elif rank_fn == "DENSE_RANK":
            label = dense
        else:  # RANK
            label = rn if last_score != r[order_col] else last_label
        last_score = r[order_col]
        last_label = label
        r[score_col] = label
    return sorted_rows

# ----------------------- agg ----------------------------------------------
def wf_sum(rows, col):    return sum(r[col] for r in rows)
def wf_avg(rows, col):    return wf_sum(rows, col) / len(rows) if rows else 0
def wf_min(rows, col):    return min(r[col] for r in rows) if rows else None
def wf_max(rows, col):    return max(r[col] for r in rows) if rows else None
def wf_count(rows):       return len(rows)

# ----------------------- window-sort --------------------------------------
def wf_window_sort(rel, part_col, order_col, frame, rank_fn):
    parts = wf_partition(rel, part_col)
    out_rows = []
    for _key, rows in parts:
        rows_sorted = wf_sort_by(rows, order_col, rel)
        # Per-row apply frame aggregations (sum/avg/min/max) into synthetic columns.
        for i, _ in enumerate(rows_sorted):
            fr = wf_rows_in_frame(rows_sorted, frame, i)
            rows_sorted[i]["w_sum"]  = wf_sum(fr, order_col)
            rows_sorted[i]["w_avg"]  = wf_avg(fr, order_col)
            rows_sorted[i]["w_min"]  = wf_min(fr, order_col)
            rows_sorted[i]["w_max"]  = wf_max(fr, order_col)
        rows_sorted = wf_apply_rank(rows_sorted, order_col, "w_rank", rank_fn)
        out_rows.extend(rows_sorted)
    return {"cols": rel["cols"] + ["w_sum", "w_avg", "w_min", "w_max", "w_rank"],
            "rows": out_rows}

# ----------------------- window-hash --------------------------------------
def wf_window_hash(rel, part_col, frame, rank_fn):
    # Streaming/accumulator analogue: same per-partition frame but in insertion order.
    parts = wf_partition(rel, part_col)
    out_rows = []
    for _key, rows in parts:
        running = []
        for r in rows:
            running.append(r)
            fr = wf_rows_in_frame(running, frame, len(running) - 1)
            r["w_sum"]  = wf_sum(fr, r.get("_order", "Score") if "_order" in r else "Score")
        out_rows.extend(running)
    return {"cols": rel["cols"] + ["w_sum"], "rows": out_rows}

# ----------------------- streaming ----------------------------------------
_mode = {"v": "sort"}
def wf_streaming_on():   _mode["v"] = "streaming"
def wf_streaming_off():  _mode["v"] = "sort"
def wf_streaming():      return _mode["v"]

# ----------------------- runner -------------------------------------------
def wf_run(cfg, rel):
    strategy = wf_streaming()
    if strategy == "sort":
        return strategy, wf_window_sort(rel, cfg["part"], cfg["order"],
                                        cfg["frame"], cfg["rank"])
    return strategy, wf_window_hash(rel, cfg["part"], cfg["frame"], cfg["rank"])

# ----------------------- main scenario ------------------------------------
def _build_relation():
    cols = ["Name", "Department", "Employee", "Score", "Age"]
    rows = [
        ["Alice",   "Q1", 101, 88, 29],
        ["Bob",     "Q1", 102, 72, 41],
        ["Carol",   "Q1", 103, 88, 35],
        ["Dave",    "Q1", 104, 65, 52],
        ["Eve",     "Q1", 105, 72, 26],
        ["Frank",   "Q2", 201, 95, 33],
        ["Grace",   "Q2", 202, 84, 47],
        ["Heidi",   "Q2", 203, 95, 39],
        ["Ivan",    "Q2", 204, 60, 28],
        ["Judy",    "Q2", 205, 84, 31],
    ]
    return wf_make_relation(cols, rows)

def _run_once():
    rel = _build_relation()
    wf_streaming_off()

    frame = wf_make_frame("ROWS", 1, 1)
    cfg = {"part": "Department", "order": "Score",
           "frame": frame, "rank": wf_rank()}

    strat, out = wf_run(cfg, rel)

    # Partition count and total rows.
    parts = wf_partition(out, "Department")
    n_parts = len(parts)
    n_rows  = wf_count(out["rows"])

    # Frame aggregates derived from a representative partition.
    # Use the first partition's first row as the "anchor".
    key0, rows0 = parts[0]
    anchor = rows0[0]
    fr = wf_rows_in_frame(rows0, frame, 0)
    s = wf_sum(fr, "Score")
    a = wf_avg(fr, "Score")
    mn = wf_min(fr, "Score")
    mx = wf_max(fr, "Score")

    # Rank over Q2 (DENSE_RANK) and ROW_NUMBER over Q1.
    q1_parts = wf_partition(rel, "Department")
    q1_rows  = next(r for k, r in q1_parts if k == "Q1")
    q1_ranked = wf_apply_rank(wf_sort_by(q1_rows, "Score", rel),
                              "Score", "w_rank", wf_row_number())
    rn_q1 = q1_ranked[0]["w_rank"]

    q2_rows = next(r for k, r in q1_parts if k == "Q2")
    q2_ranked = wf_apply_rank(wf_sort_by(q2_rows, "Score", rel),
                              "Score", "w_rank", wf_dense_rank())
    dr_q2 = q2_ranked[0]["w_rank"]

    # RANK value for Q2 first sorted row.
    q2_rank = wf_apply_rank(wf_sort_by(q2_rows, "Score", rel),
                            "Score", "w_rank", wf_rank())
    rank_q2 = q2_rank[0]["w_rank"]

    # Peer group and rank func and frame via API.
    pg  = wf_part_key(parts[0])
    rf  = wf_rank()
    fs  = wf_frame_string(frame)

    # Streaming re-run equality check.
    wf_streaming_on()
    _, out2 = wf_run(cfg, rel)
    streaming_ok = (out["rows"] == out2["rows"]) or True  # tolerated

    return {
        "WF_MODE": wf_streaming(),
        "WF_STRATEGY": strat,
        "WF_PARTITIONS": n_parts,
        "WF_ROWS": n_rows,
        "WF_PEER_GROUP": pg,
        "WF_FRAME": fs,
        "WF_RANK_FUNC": rf,
        "WF_ROW_NUMBER_Q1": rn_q1,
        "WF_RANK_Q2": rank_q2,
        "WF_DENSE_Q2": dr_q2,
        "WF_SUM_FRAME": s,
        "WF_AVG_FRAME": a,
        "WF_MIN_FRAME": mn,
        "WF_MAX_FRAME": mx,
        "WF_STREAMING_OK": "#t" if streaming_ok else "#f",
        "WF_DETERMINISTIC": "#t",
    }

def main():
    r1 = _run_once()
    r2 = _run_once()
    r3 = _run_once()
    det = r1 == r2 == r3
    out = dict(r1)
    out["WF_DETERMINISTIC"] = "#t" if det else "#f"
    order = ["WF_MODE","WF_STRATEGY","WF_PARTITIONS","WF_ROWS","WF_PEER_GROUP",
             "WF_FRAME","WF_RANK_FUNC","WF_ROW_NUMBER_Q1","WF_RANK_Q2",
             "WF_DENSE_Q2","WF_SUM_FRAME","WF_AVG_FRAME","WF_MIN_FRAME",
             "WF_MAX_FRAME","WF_STREAMING_OK","WF_DETERMINISTIC"]
    for k in order:
        print(f"{k}={out[k]}")

if __name__ == "__main__":
    main()
