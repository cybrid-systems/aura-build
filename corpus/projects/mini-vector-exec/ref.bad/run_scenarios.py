# Mini reference implementation of the mini-vector-exec Aura scenario.
# This is a self-contained Python 3 script that mimics the Aura pipeline:
#   SCAN -> FILTER -> PROJECT -> AGGREGATE -> MERGE
# with runtime-adaptive batch sizing (governor) and late materialization hints.
#
# Stdlib only.

import sys


# -------- types.aura --------
class Batch:
    """A simple batch of rows. Rows are tuples; width is number of columns."""
    __slots__ = ("rows", "width")

    def __init__(self, rows, width):
        self.rows = list(rows)
        self.width = width


def make_batch(rows, width):
    return Batch(rows, width)


def batch_add_row(b, row):
    b.rows.append(row)


def batch_rows(b):
    return b.rows


def batch_width(b):
    return b.width


def batch_empty(b):
    return len(b.rows) == 0


# -------- schema.aura --------
COLS = ("colA", "colB", "colC", "colD", "id")
COL_INDEX = {name: i for i, name in enumerate(COLS)}
LATE_COLS = ("colC",)  # selectively materialized


def schema_cols():
    return COLS


def schema_col_index(name):
    return COL_INDEX[name]


def schema_late_cols():
    return LATE_COLS


# -------- source.aura --------
ROW_COUNT = 10_000
COLS_TOTAL = len(COLS)


def source_row_count():
    return ROW_COUNT


def source_row(i):
    # Deterministic synthetic data:
    # colA = i * 7 mod 1000
    # colB = i % 37
    # colC = (i * 13) % 200
    # colD = (i // 50)
    # id   = i
    colA = (i * 7) % 1000
    colB = i % 37
    colC = (i * 13) % 200
    colD = i // 50
    rid = i
    return (colA, colB, colC, colD, rid)


def source_cols():
    return COLS


# -------- config.aura --------
def config_batch_min():
    return 64


def config_batch_max():
    return 4096


def config_batch_init():
    return 256


def config_mode():
    return "PULL"


# -------- governor.aura --------
class Governor:
    def __init__(self, init, lo, hi):
        self.size = init
        self.lo = lo
        self.hi = hi
        self.mode = "ADAPTIVE"

    def observe(self, width):
        # Adaptive sizing: if observed width is large, shrink batch;
        # if observed width is small, grow batch (bounded).
        target = max(1, 8192 // max(1, width))
        self.size = max(self.lo, min(self.hi, target))

    def batch_size(self):
        return self.size

    def gov_mode(self):
        return self.mode


def gov_init(init, lo, hi):
    return Governor(init, lo, hi)


def gov_observe(g, width):
    g.observe(width)


def gov_batch_size(g):
    return g.batch_size()


def gov_mode(g):
    return g.gov_mode()


# -------- late.aura --------
def late_needed(col_name):
    return col_name in LATE_COLS


def late_emit(batch, schema_cols_list):
    # Mark late columns as None in the emitted batch so the consumer
    # knows they need re-materialization on demand.
    late_idx = {COL_INDEX[c] for c in LATE_COLS if c in COL_INDEX}
    out_rows = []
    for row in batch_rows(batch):
        new_row = list(row)
        for idx in late_idx:
            new_row[idx] = None
        out_rows.append(tuple(new_row))
    return Batch(out_rows, batch.width)


def late_project_others(batch, projected_names):
    # Keep non-late columns fully populated; late ones are placeholders.
    keep_idx = [COL_INDEX[n] for n in projected_names if n in COL_INDEX]
    new_rows = [tuple(r[i] for i in keep_idx) for r in batch_rows(batch)]
    return Batch(new_rows, len(keep_idx))


# -------- scan.aura --------
class Scan:
    def __init__(self):
        self.i = 0
        self.open_state = False


def make_scan():
    return Scan()


def scan_open(s):
    s.i = 0
    s.open_state = True
    return True


def scan_next(s, batch_size):
    if not s.open_state:
        return None
    if s.i >= ROW_COUNT:
        s.open_state = False
        return None
    take = min(batch_size, ROW_COUNT - s.i)
    rows = [source_row(s.i + k) for k in range(take)]
    s.i += take
    b = make_batch(rows, COLS_TOTAL)
    return b


def scan_close(s):
    s.open_state = False


# -------- filter.aura --------
class Filter:
    def __init__(self, child, pred, col_name):
        self.child = child
        self.pred = pred
        self.col_name = col_name
        self.col_idx = COL_INDEX[col_name]
        self.open_state = False
        self.buf = []
        self.buf_pos = 0

    def _refill(self, batch_size):
        self.buf = []
        self.buf_pos = 0
        while True:
            b = scan_next(self.child, batch_size) if hasattr(self.child, "next_batch") else self.child.next(batch_size)
            if b is None:
                return
            for r in batch_rows(b):
                if self.pred(r[self.col_idx]):
                    self.buf.append(r)
                    if len(self.buf) >= batch_size:
                        return


def make_filter(child, pred, col_name):
    return Filter(child, pred, col_name)


def filter_open(f):
    f.open_state = True
    if hasattr(f.child, "open"):
        f.child.open()
    return True


def filter_next(f, batch_size):
    if not f.open_state:
        return None
    if f.buf_pos >= len(f.buf):
        f._refill(batch_size)
    if not f.buf:
        f.open_state = False
        return None
    take = min(batch_size, len(f.buf) - f.buf_pos)
    rows = f.buf[f.buf_pos:f.buf_pos + take]
    f.buf_pos += take
    return make_batch(rows, f.col_idx if False else COLS_TOTAL)


def filter_close(f):
    f.open_state = False
    if hasattr(f.child, "close"):
        f.child.close()


# -------- project.aura --------
class Project:
    def __init__(self, child, names):
        self.child = child
        self.names = names
        self.idx = [COL_INDEX[n] for n in names]
        self.width = len(names)
        self.open_state = False

    def open(self):
        self.open_state = True
        if hasattr(self.child, "open"):
            self.child.open()
        return True


def make_project(child, names):
    return Project(child, names)


def project_open(p):
    return p.open()


def project_next(p, batch_size):
    if not p.open_state:
        return None
    b = p.child.next(batch_size)
    if b is None:
        p.open_state = False
        return None
    rows = [tuple(r[i] for i in p.idx) for r in batch_rows(b)]
    return make_batch(rows, p.width)


def project_close(p):
    p.open_state = False
    if hasattr(p.child, "close"):
        p.child.close()


# -------- aggregate.aura --------
class Aggregate:
    """Groups by colB (index 1), computes count. Emits one row per group at end."""
    def __init__(self, child, group_col, agg_name="count"):
        self.child = child
        self.group_col = group_col
        self.group_idx = COL_INDEX[group_col]
        self.agg_name = agg_name
        self.open_state = False
        self.groups = {}

    def open(self):
        self.open_state = True
        self.groups = {}
        if hasattr(self.child, "open"):
            self.child.open()
        return True

    def close(self):
        self.open_state = False
        if hasattr(self.child, "close"):
            self.child.close()


def make_aggregate(child, group_col, agg_name="count"):
    return Aggregate(child, group_col, agg_name)


def aggregate_open(a):
    return a.open()


def aggregate_next(a, batch_size):
    if not a.open_state:
        return None
    # Pull all child batches.
    while True:
        b = a.child.next(batch_size)
        if b is None:
            break
        for r in batch_rows(b):
            key = r[a.group_idx]
            cur = a.groups.get(key)
            if cur is None:
                a.groups[key] = 1
            else:
                a.groups[key] = cur + 1
    # Emit aggregated rows as a single batch: (colB, count)
    rows = [(k, v) for k, v in a.groups.items()]
    a.open_state = False
    if not rows:
        return None
    return make_batch(rows, 2)


def aggregate_close(a):
    a.close()


# -------- merge.aura --------
class Merge:
    """Merges two child streams by interleaving batches round-robin."""
    def __init__(self, left, right):
        self.left = left
        self.right = right
        self.open_state = False
        self.turn = 0  # 0 = left, 1 = right
        self.left_done = False
        self.right_done = False

    def open(self):
        self.open_state = True
        self.turn = 0
        self.left_done = False
        self.right_done = False
        if hasattr(self.left, "open"):
            self.left.open()
        if hasattr(self.right, "open"):
            self.right.open()
        return True


def make_merge(left, right):
    return Merge(left, right)


def merge_open(m):
    return m.open()


def merge_next(m, batch_size):
    if not m.open_state:
        return None
    # Alternate children each call; emit whichever side has rows.
    for _ in range(2):
        if m.turn == 0:
            if m.left_done:
                m.turn = 1
                continue
            b = m.left.next(batch_size)
            if b is None:
                m.left_done = True
                m.turn = 1
                continue
            m.turn = 1
            return b
        else:
            if m.right_done:
                m.turn = 0
                continue
            b = m.right.next(batch_size)
            if b is None:
                m.right_done = True
                m.turn = 0
                continue
            m.turn = 0
            return b
    m.open_state = False
    return None


def merge_close(m):
    m.open_state = False
    if hasattr(m.left, "close"):
        m.left.close()
    if hasattr(m.right, "close"):
        m.right.close()


# -------- pipeline.aura --------
def _attach_next(operator):
    """Ensure operator has a .next(batch_size) method (Volcano interface)."""
    name = type(operator).__name__
    if name == "Scan":
        operator.next = lambda bs: scan_next(operator, bs)
        operator.open = lambda: scan_open(operator)
        operator.close = lambda: scan_close(operator)
    elif name == "Filter":
        operator.next = lambda bs: filter_next(operator, bs)
        operator.open = lambda: filter_open(operator)
        operator.close = lambda: filter_close(operator)
    elif name == "Project":
        operator.next = lambda bs: project_next(operator, bs)
        operator.open = lambda: project_open(operator)
        operator.close = lambda: project_close(operator)
    elif name == "Aggregate":
        operator.next = lambda bs: aggregate_next(operator, bs)
        operator.open = lambda: aggregate_open(operator)
        operator.close = lambda: aggregate_close(operator)
    elif name == "Merge":
        operator.next = lambda bs: merge_next(operator, bs)
        operator.open = lambda: merge_open(operator)
        operator.close = lambda: merge_close(operator)
    return operator


STAGE_NAMES = ("SCAN", "FILTER", "PROJECT", "AGGREGATE", "MERGE")


def pipeline_stage_names():
    return STAGE_NAMES


class PipelineStats:
    def __init__(self):
        self.rows_scanned = 0
        self.rows_after_filter = 0
        self.rows_projected = 0
        self.rows_aggregated = 0

    def as_dict(self):
        return {
            "rows_scanned": self.rows_scanned,
            "rows_after_filter": self.rows_after_filter,
            "rows_projected": self.rows_projected,
            "rows_aggregated": self.rows_aggregated,
        }


def pipeline_run_stats(s):
    return s.as_dict()


def pipeline_execute(root, governor):
    """Drives the volcano-style pipeline; observes batch widths via governor
    and applies late materialization via late-emit on each yielded batch."""
    root.open()
    stats = PipelineStats()
    bs = governor.batch_size()
    # Track per-stage operator references by walking children.
    # We assume root is a Merge with left = Aggregate(left=Project(left=Filter(left=Scan))), right = similar.
    # For stat accumulation, we instrument the intermediate operators by
    # wrapping their .next methods.
    _instrument(root, stats)
    emitted = 0
    while True:
        b = root.next(bs)
        if b is None:
            break
        gov_observe(governor, b.width)
        bs = governor.batch_size()
        _ = late_emit(b, COLS)
        emitted += 1
    root.close()
    return stats, emitted


def _instrument(op, stats):
    """Wrap op.next to accumulate per-stage row counts into stats."""
    name = type(op).__name__
    orig_next = op.next
    if name == "Scan":
        def wrapped(bs):
            b = orig_next(bs)
            if b is not None:
                stats.rows_scanned += len(batch_rows(b))
            return b
        op.next = wrapped
    elif name == "Filter":
        def wrapped(bs):
            b = orig_next(bs)
            if b is not None:
                stats.rows_after_filter += len(batch_rows(b))
            return b
        op.next = wrapped
    elif name == "Project":
        def wrapped(bs):
            b = orig_next(bs)
            if b is not None:
                stats.rows_projected += len(batch_rows(b))
            return b
        op.next = wrapped
    elif name == "Aggregate":
        def wrapped(bs):
            b = orig_next(bs)
            if b is not None:
                stats.rows_aggregated += len(batch_rows(b))
            return b
        op.next = wrapped
    elif name == "Merge":
        # Recurse into children; Merge itself doesn't change row count.
        _instrument(op.left, stats)
        _instrument(op.right, stats)


# -------- main.aura --------
def main_run():
    # Step 1: config
    gov_min = config_batch_min()
    gov_max = config_batch_max()
    gov_init_size = config_batch_init()
    mode = config_mode()

    # Step 2: governor
    gov = gov_init(gov_init_size, gov_min, gov_max)

    # Step 3-6: build two pipelines (even/odd id) wrapped in merge.
    def build_pipeline(id_filter):
        scan = _attach_next(make_scan())
        flt = _attach_next(make_filter(scan, id_filter, "id"))
        # Project: keep (colB, colA, colD) per the GOAL step 5.
        proj = _attach_next(make_project(flt, ("colB", "colA", "colD")))
        agg = _attach_next(make_aggregate(proj, "colB", "count"))
        return agg

    even_pipe = build_pipeline(lambda v: (v % 2) == 0)
    odd_pipe = build_pipeline(lambda v: (v % 2) == 1)

    root = _attach_next(make_merge(even_pipe, odd_pipe))

    # Step 7-8: execute
    stats, emitted_batches = pipeline_execute(root, gov)

    # Step 9: stage names
    stages = pipeline_stage_names()

    # Print contract.
    out = []
    for s in stages:
        out.append(f"STAGE={s}")
    out.append("BATCH_GOV=ADAPTIVE")
    out.append(f"BATCH_GOV_MIN={gov_min}")
    out.append(f"BATCH_GOV_MAX={gov_max}")
    out.append(f"BATCH_GOV_INIT={gov_init_size}")
    out.append(f"LATE_MAT={schema_late_cols()[0]}")
    rs = pipeline_run_stats(stats)
    out.append(f"ROWS_SCANNED={rs['rows_scanned']}")
    out.append(f"ROWS_AFTER_FILTER={rs['rows_after_filter']}")
    out.append(f"ROWS_PROJECTED={rs['rows_projected']}")
    out.append(f"ROWS_AGGREGATED={rs['rows_aggregated']}")
    out.append(f"EXEC_MODE={mode}")
    out.append("PHASE=DONE")

    sys.stdout.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main_run()
