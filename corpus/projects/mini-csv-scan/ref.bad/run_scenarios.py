#!/usr/bin/env python3
"""Toy columnar CSV scan engine in pure Python, mirroring the Aura scenario."""
import time

# ---------- types.aura ----------
def define_record_column(name, values):
    return {"name": name, "values": list(values)}

def col_name(c): return c["name"]
def col_values(c): return c["values"]

def make_batch(cols, rows):
    # cols: list of (name, values-list); rows: number of rows in batch
    return {"cols": cols, "rows": rows}

def batch_cols(b): return b["cols"]
def batch_row_count(b): return b["rows"]

# ---------- datasource.aura ----------
def make_rows_source(header, rows):
    return {"header": list(header), "rows": [list(r) for r in rows]}

def source_header(s): return s["header"]
def source_rows(s): return s["rows"]
def source_row_count(s): return len(s["rows"])

# ---------- parser.aura ----------
NULL_TOKENS = {"", "null", "NULL", "Null", "none", "None"}

def is_null_cell(s): return s in NULL_TOKENS

def parse_cell(s):
    if is_null_cell(s): return None
    try:
        if "." in s:
            return float(s)
        return int(s)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            return s

def parse_row(header, line):
    return {h: parse_cell(v) for h, v in zip(header, line)}

def cell_to_number(s):
    if isinstance(s, (int, float)): return s
    if is_null_cell(s): return None
    return parse_cell(s)

# ---------- projection.aura ----------
def make_projection(col_names):
    return {"cols": list(col_names)}

def projection_cols(p): return p["cols"]

def project_source(src, p):
    header = source_header(src)
    rows = source_rows(src)
    idx = [header.index(c) for c in projection_cols(p)]
    new_header = [header[i] for i in idx]
    new_rows = [[r[i] for i in idx] for r in rows]
    return make_rows_source(new_header, new_rows)

def project_batch(b, p):
    wanted = projection_cols(p)
    new_cols = []
    for c in batch_cols(b):
        if col_name(c) in wanted:
            new_cols.append(c)
    return make_batch(new_cols, batch_row_count(b))

# ---------- predicates.aura ----------
def make_predicate(col, op, value):
    return {"col": col, "op": op, "value": value}

def predicate_col(p): return p["col"]
def predicate_op(p): return p["op"]
def predicate_value(p): return p["value"]

def eval_predicate(pred, cell):
    v = predicate_value(pred)
    if cell is None: return False
    op = predicate_op(pred)
    try:
        a, b = cell, v
        if op == "=":  return a == b
        if op == "!=": return a != b
        if op == "<":  return a <  b
        if op == "<=": return a <= b
        if op == ">":  return a >  b
        if op == ">=": return a >= b
    except TypeError:
        return False
    return False

def filter_batch(b, pred):
    col = next((c for c in batch_cols(b) if col_name(c) == predicate_col(pred)), None)
    if col is None: return b
    keep = [i for i, v in enumerate(col_values(col)) if eval_predicate(pred, v)]
    new_cols = []
    for c in batch_cols(b):
        cv = col_values(c)
        new_cols.append(define_record_column(col_name(c), [cv[i] for i in keep]))
    return make_batch(new_cols, len(keep))

# ---------- pushdown.aura ----------
PUSHDOWN_OPS = {"=", "!=", "<", "<=", ">", ">="}

def pushdown_applicable(p):
    return predicate_op(p) in PUSHDOWN_OPS and not is_null_cell(str(predicate_value(p)))

def extract_pushdown(header, preds):
    applicable = [p for p in preds if pushdown_applicable(p) and predicate_col(p) in header]
    return {"preds": applicable}

def pushdown_count(p): return len(p["preds"])

def apply_pushdown(src, p):
    header = source_header(src)
    rows = source_rows(src)
    for pred in p["preds"]:
        c = predicate_col(pred)
        if c not in header: continue
        ci = header.index(c)
        rows = [r for r in rows if eval_predicate(pred, r[ci])]
        header = header  # unchanged
    return make_rows_source(header, rows)

# ---------- aggregates.aura ----------
def make_aggregator(cols):
    return {c: {"count": 0, "sum": 0, "min": None, "max": None, "nulls": 0}
            for c in cols}

def aggregator_cols(a): return list(a.keys())

def agg_update(a, col_name, vals):
    if col_name not in a: return
    s = a[col_name]
    for v in vals:
        if v is None:
            s["nulls"] += 1
            continue
        s["count"] += 1
        if isinstance(v, (int, float)):
            s["sum"] += v
            s["min"] = v if s["min"] is None else min(s["min"], v)
            s["max"] = v if s["max"] is None else max(s["max"], v)

def agg_count(a, c):    return a[c]["count"]
def agg_sum(a, c):      return a[c]["sum"]
def agg_min(a, c):      return a[c]["min"]
def agg_max(a, c):      return a[c]["max"]
def agg_nulls(a, c):    return a[c]["nulls"]

# ---------- batcher.aura ----------
def make_batcher(size): return {"size": size}
def batcher_size(b): return b["size"]

def batchify(rows, size):
    return [rows[i:i+size] for i in range(0, len(rows), size)]

def rows_to_batches(src, size):
    header = source_header(src)
    rows = source_rows(src)
    raw = batchify(rows, size)
    out = []
    for chunk in raw:
        cols = []
        for i, h in enumerate(header):
            cols.append(define_record_column(h, [r[i] for r in chunk]))
        out.append(make_batch(cols, len(chunk)))
    return out

# ---------- stats.aura ----------
def make_stats(): return {"rows_scanned": 0, "rows_passed": 0, "batches": 0, "ticks": 0}

def stats_tick(s, rows_passed, rows_scanned):
    s["rows_scanned"] += rows_scanned
    s["rows_passed"]   += rows_passed
    s["batches"]       += 1
    s["ticks"]         += 1

def stats_rows_scanned(s): return s["rows_scanned"]
def stats_rows_passed(s):  return s["rows_passed"]
def stats_batches(s):      return s["batches"]

def stats_elapsed_us(s, start, end):
    # Aura semantics: microseconds between monotonic-ish start/end
    return int(round((end - start) * 1_000_000))

# ---------- scanner.aura ----------
def make_scan(source, projection, predicates, batch_size):
    return {
        "source": source,
        "projection": projection,
        "predicates": predicates,
        "batch_size": batch_size,
        "agg": None,
        "stats": make_stats(),
        "rows_passed": 0,
        "batches_emitted": 0,
    }

def scan_run(scan):
    src = scan["source"]
    proj = scan["projection"]
    preds = scan["predicates"]
    batcher = make_batcher(scan["batch_size"])

    # Aggregate over projected columns (per GOAL: iterate aggregator's column list)
    cols = projection_cols(proj)
    agg = make_aggregator(cols)
    scan["agg"] = agg

    # Materialize column-oriented batches from the source
    batches = rows_to_batches(src, batcher_size(batcher))
    scan["batches_emitted"] = len(batches)

    start = time.perf_counter()
    for b in batches:
        # 1. project to requested columns (still columnar)
        pb = project_batch(b, proj)
        # 2. evaluate predicates over the projected batch (per-cell column scan)
        keep_idx = list(range(batch_row_count(pb)))
        for pred in preds:
            col = next((c for c in batch_cols(pb) if col_name(c) == predicate_col(pred)), None)
            if col is None: continue
            cv = col_values(col)
            keep_idx = [i for i in keep_idx if eval_predicate(pred, cv[i])]
        if keep_idx:
            kept_cols = []
            for c in batch_cols(pb):
                cv = col_values(c)
                kept_cols.append(define_record_column(col_name(c), [cv[i] for i in keep_idx]))
            kept = make_batch(kept_cols, len(keep_idx))
        else:
            kept = make_batch([define_record_column(c, []) for c in cols], 0)

        # 3. update aggregates per column
        for c in batch_cols(kept):
            agg_update(agg, col_name(c), col_values(c))

        # 4. tick stats
        stats_tick(scan["stats"], batch_row_count(kept), batch_row_count(b))
        scan["rows_passed"] += batch_row_count(kept)

    end = time.perf_counter()
    scan["stats_elapsed_us"] = stats_elapsed_us(scan["stats"], start, end)
    return scan

def scan_stats(scan): return scan["stats"]
def scan_rows_passed(scan): return scan["rows_passed"]

# ---------- reporter.aura ----------
def report_key_value(k, v):
    return f"{k}={v}"

def format_scan_report(stats, source, projection, pushdown_count, batches_passed):
    # Note: batches_passed here is the total number of emitted batches from the scan
    lines = []
    lines.append(report_key_value("scan.source_rows", source_row_count(source)))
    lines.append(report_key_value("scan.projected_cols", ",".join(projection_cols(projection))))
    lines.append(report_key_value("scan.pushdown_predicates", str(pushdown_count)))
    lines.append(report_key_value("scan.batches_emitted", batches_passed))
    lines.append(report_key_value("scan.rows_scanned", stats_rows_scanned(stats)))
    lines.append(report_key_value("scan.rows_passed", stats_rows_passed(stats)))
    return lines

def print_report(lines):
    for l in lines:
        print(l)

# ---------- main.aura ----------
def main():
    # 1. small in-memory CSV
    header = ("id", "price", "qty", "region")
    raw_rows = [
        ("1",  "12",  "50",  "us"),
        ("2",  "8",   "120", "eu"),
        ("3",  "20",  "30",  "us"),
        ("4",  "5",   "75",  "apac"),
        ("5",  "15",  "200", "eu"),
        ("6",  "10",  "10",  "us"),
        ("7",  "30",  "5",   "apac"),
        ("8",  "null","40",  "us"),
        ("9",  "18",  "60",  "eu"),
        ("10", "7",   "90",  "us"),
    ]

    # 2. build datasource
    src = make_rows_source(header, raw_rows)

    # 3. projection: price, qty
    proj = make_projection(("price", "qty"))

    # 4. predicates
    preds = [
        make_predicate("price", ">=", 10),
        make_predicate("qty",   "<", 100),
    ]

    # 5. extract pushdown predicates
    pd = extract_pushdown(source_header(src), preds)

    # 6. apply pushdown
    src = apply_pushdown(src, pd)

    # 7. batcher
    batcher = make_batcher(3)
    # (rows->batches is invoked inside scan_run via the batcher size, mirroring the Aura call)

    # 8. scan
    scan = make_scan(src, proj, preds, batcher_size(batcher))
    scan_run(scan)

    # 9. per-column aggregates (iterate aggregator's column list — anti-hardcode)
    lines = format_scan_report(
        scan_stats(scan),
        src,
        proj,
        pushdown_count(pd),
        scan["batches_emitted"],
    )

    for c in aggregator_cols(scan["agg"]):
        lines.append(report_key_value(f"scan.col.{c}.count", agg_count(scan["agg"], c)))
        lines.append(report_key_value(f"scan.col.{c}.sum",   agg_sum(scan["agg"], c)))
        lines.append(report_key_value(f"scan.col.{c}.min",   agg_min(scan["agg"], c)))
        lines.append(report_key_value(f"scan.col.{c}.max",   agg_max(scan["agg"], c)))
        lines.append(report_key_value(f"scan.col.{c}.nulls", agg_nulls(scan["agg"], c)))

    lines.append(report_key_value("scan.elapsed_us", scan["stats_elapsed_us"]))
    lines.append(report_key_value("scan.status", "OK"))

    print_report(lines)

if __name__ == "__main__":
    main()
