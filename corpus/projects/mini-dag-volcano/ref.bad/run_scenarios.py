#!/usr/bin/env python3
"""Reference Python implementation for mini-dag-volcano GOAL scenario."""

# Standard in-memory semantics for the Aura DAG-scheduled Volcano engine.

# ---------- op.aura ----------
def op_make(name, kind, inputs):
    return {"name": name, "kind": kind, "inputs": list(inputs), "rows": 0}

def op_name(op): return op["name"]
def op_kind(op): return op["kind"]
def op_inputs(op): return list(op["inputs"])
def op_rows(op): return op["rows"]
def op_add_rows(op, n):
    op["rows"] = op["rows"] + n

# ---------- plan.aura ----------
def plan_build(ops, edges):
    # Returns an alist-like dict with nodes and edges; topo-validity computed on demand.
    return {"nodes": list(ops), "edges": list(edges)}

def plan_nodes(p): return list(p["nodes"])
def plan_edges(p): return list(p["edges"])

def _toposort_helper(nodes, edges):
    by_name = {op_name(n): n for n in nodes}
    out = [[] for _ in range(len(by_name))]
    indeg = {nm: 0 for nm in by_name}
    for a, b in edges:
        if b in indeg:
            indeg[b] += 1
        if a in by_name:
            out[list(by_name.keys()).index(a)].append(b)
    # Kahn's algorithm
    queue = [nm for nm, d in indeg.items() if d == 0]
    order = []
    while queue:
        queue.sort()  # deterministic
        n = queue.pop(0)
        order.append(n)
        for nm in by_name:
            pass
    # Build reverse-edge map
    rev = {nm: [] for nm in by_name}
    for a, b in edges:
        if a in rev:
            rev[a].append(b)
    queue = [nm for nm, d in indeg.items() if d == 0]
    order = []
    adj = {nm: [] for nm in by_name}
    for a, b in edges:
        if a in adj:
            adj[a].append(b)
    indeg2 = {nm: 0 for nm in by_name}
    for a, b in edges:
        if b in indeg2:
            indeg2[b] += 1
    q = sorted([nm for nm, d in indeg2.items() if d == 0])
    while q:
        q.sort()
        n = q.pop(0)
        order.append(n)
        for m in adj.get(n, []):
            indeg2[m] -= 1
            if indeg2[m] == 0:
                q.append(m)
    return order

def plan_valid(p):
    nodes = plan_nodes(p)
    edges = plan_edges(p)
    order = _toposort_helper(nodes, edges)
    # Detect cycle: order misses nodes if cycle exists.
    return len(order) == len(nodes)

# ---------- toposort.aura ----------
def toposort(nodes, edges):
    return _toposort_helper(nodes, edges)

def toposort_detect_cycle(nodes, edges):
    order = _toposort_helper(nodes, edges)
    return len(order) != len(nodes)

# ---------- breaker.aura ----------
_BREAKERS = {"aggregate", "join"}

def breaker(kind):
    return kind in _BREAKERS

def breaker_kinds():
    return list(_BREAKERS)

# ---------- fragment.aura ----------
def fragment_build(topo, breakers_set):
    # Topo is a list of op names; breakers_set is a set of operator names that are breakers.
    fragments = []
    current = []
    for nm in topo:
        if nm in breakers_set and current:
            fragments.append(current)
            current = [nm]
        else:
            current.append(nm)
    if current:
        fragments.append(current)
    return fragments

def fragment_count(frags):
    return len(frags)

# ---------- morsel.aura ----------
MORSEL_SIZE = 64

def morsel_size():
    return MORSEL_SIZE

def morsel_slice(rows, size):
    out = []
    for i in range(0, len(rows), size):
        out.append(rows[i:i+size])
    return out

# ---------- rowbuf.aura ----------
def rowbuf_new():
    return []

def rowbuf_push(buf, rows):
    buf.extend(rows)

def rowbuf_drain(buf):
    out = list(buf)
    buf.clear()
    return out

def rowbuf_count(buf):
    return len(buf)

# ---------- scan_op.aura ----------
def scan_emit(op, n):
    base = op_rows(op)
    return [base + i + 1 for i in range(n)]

# ---------- filter_op.aura ----------
def filter_emit(rows):
    # Even-only filter (modulo-2).
    return [r for r in rows if (r % 2) == 0]

# ---------- join_op.aura ----------
def join_emit(left_rows, right_rows):
    # Paired/cartesian-reduced: take zip, length = min(len(L), len(R)).
    n = min(len(left_rows), len(right_rows))
    out = []
    for i in range(n):
        out.append((left_rows[i], right_rows[i]))
    return out

# ---------- metrics.aura ----------
def metrics_init():
    return {"ticks": 0, "per_op": {}, "sunk_rows": 0}

def metrics_tick(m):
    m["ticks"] += 1

def metrics_record(m, op_name, rows):
    if op_name not in m["per_op"]:
        m["per_op"][op_name] = 0
    m["per_op"][op_name] += len(rows)

def metrics_snapshot(m):
    return dict(m)

# ---------- sched.aura ----------
def sched_ready(frag, state):
    # A fragment is ready if any op in it (except the first) has data pending,
    # or its first op is a scan with no parent waiting.
    # Simplified: ready when at least one buffer in the fragment has data
    # OR the fragment's leftmost op is a scan capable of emitting.
    buffers = state["buffers"]
    ops_by_name = state["ops_by_name"]
    for nm in frag:
        op = ops_by_name[nm]
        if op_kind(op) == "scan":
            # Scan can emit if no upstream needed; readiness = no upstream buffer waiting.
            upstream_done = True
            for inp in op_inputs(op):
                if rowbuf_count(buffers[inp]) > 0:
                    upstream_done = False
                    break
            if upstream_done:
                return True
        else:
            if rowbuf_count(buffers[nm]) > 0:
                return True
    return False

def sched_step(frags, state):
    buffers = state["buffers"]
    ops_by_name = state["ops_by_name"]
    metrics = state["metrics"]
    MS = state["morsel_size"]

    any_progress = False
    for frag in frags:
        for nm in frag:
            op = ops_by_name[nm]
            kind = op_kind(op)
            if kind == "scan":
                # Emit one morsel of MS rows.
                rows = scan_emit(op, MS)
                op_add_rows(op, len(rows))
                metrics_record(metrics, nm, rows)
                # Push to children (successors).
                children = state["successors"].get(nm, [])
                for c in children:
                    rowbuf_push(buffers[c], rows)
                any_progress = True
            else:
                # Pull from upstream input(s) (drainable since break occurs at breakers).
                if not breaker(kind):
                    # Non-breaker: just pull one morsel from each input.
                    consumed_any = False
                    for inp in op_inputs(op):
                        buf = buffers[inp]
                        avail = rowbuf_count(buf)
                        if avail > 0:
                            take = min(MS, avail)
                            chunk = buf[:take]
                            del buf[:take]
                            consumed_any = True
                            # process locally
                            rows_in = chunk
                            if kind == "filter":
                                rows_out = filter_emit(rows_in)
                            elif kind == "project":
                                rows_out = [(r,) for r in rows_in]
                            elif kind == "sink":
                                rows_out = list(rows_in)
                            else:
                                rows_out = list(rows_in)
                            op_add_rows(op, len(rows_out))
                            metrics_record(metrics, nm, rows_out)
                            if kind == "sink":
                                metrics["sunk_rows"] += len(rows_out)
                            # push to successors
                            for c in state["successors"].get(nm, []):
                                rowbuf_push(buffers[c], rows_out)
                    if consumed_any:
                        any_progress = True
                else:
                    # Breaker: drains all available rows from each input, then processes.
                    drained_any = False
                    all_in = []
                    for inp in op_inputs(op):
                        rows_in = rowbuf_drain(buffers[inp])
                        if rows_in:
                            drained_any = True
                        all_in.append(rows_in)
                    if drained_any:
                        any_progress = True
                        if kind == "join":
                            # join has 2 inputs (left, right); pair them.
                            if len(all_in) >= 2:
                                rows_out = join_emit(all_in[0], all_in[1])
                            else:
                                rows_out = []
                        elif kind == "aggregate":
                            # Aggregate: group by 8 (count modulo-8 bucketed).
                            buckets = {}
                            for r in all_in[0]:
                                k = r % 8
                                buckets[k] = buckets.get(k, 0) + 1
                            rows_out = [(k, v) for k, v in sorted(buckets.items())]
                            # Padded to 8 buckets.
                            full = {i: buckets.get(i, 0) for i in range(8)}
                            rows_out = [(k, full[k]) for k in range(8)]
                        else:
                            rows_out = []
                        op_add_rows(op, len(rows_out))
                        metrics_record(metrics, nm, rows_out)
                        for c in state["successors"].get(nm, []):
                            rowbuf_push(buffers[c], rows_out)
    if any_progress:
        metrics_tick(metrics)
    return any_progress

# ---------- exec.aura ----------
def exec_run(plan, morsel_size):
    ops = plan_nodes(plan)
    edges = plan_edges(plan)
    ops_by_name = {op_name(o): o for o in ops}

    # Build successor map.
    successors = {op_name(o): [] for o in ops}
    predecessors = {op_name(o): [] for o in ops}
    for a, b in edges:
        successors[a].append(b)
        predecessors[b].append(a)

    # Topological order of names.
    topo_names = toposort(ops, edges)

    # Identify breakers by name (use node kind).
    breakers_named = set(op_name(o) for o in ops if breaker(op_kind(o)))

    # Build fragments.
    frags = fragment_build(topo_names, breakers_named)

    # Initialize buffers per op.
    buffers = {op_name(o): rowbuf_new() for o in ops}

    metrics = metrics_init()
    state = {
        "buffers": buffers,
        "ops_by_name": ops_by_name,
        "successors": successors,
        "predecessors": predecessors,
        "metrics": metrics,
        "morsel_size": morsel_size,
    }

    # Tick loop: run until no progress.
    # Bound iterations to avoid infinite loops in pathological plans.
    MAX_TICKS = 10000
    i = 0
    while i < MAX_TICKS:
        progressed = sched_step(frags, state)
        if not progressed:
            break
        i += 1

    return {
        "ticks": metrics["ticks"],
        "fragments": frags,
        "per_op_rows": {k: v for k, v in metrics["per_op"].items()},
        "sunk_rows": metrics["sunk_rows"],
    }

# ---------- report.aura ----------
def report_format(metrics_result, plan, frags):
    ops = plan_nodes(plan)
    edges = plan_edges(plan)
    nodes_count = len(ops)
    edges_count = len(edges)
    cycles = toposort_detect_cycle(ops, edges)
    topo = toposort(ops, edges)
    breakers_list = [op_name(o) for o in ops if breaker(op_kind(o))]
    fragments_count = fragment_count(frags)
    MS = morsel_size()
    ticks = metrics_result["ticks"]
    per_op = metrics_result["per_op_rows"]
    sunk = metrics_result["sunk_rows"]

    # Per-stage row counts in canonical topo order:
    canonical = ["scan1", "filter", "project", "scan2", "join", "aggregate", "sink"]
    scan1_rows = per_op.get("scan1", 0)
    scan2_rows = per_op.get("scan2", 0)
    filter_rows = per_op.get("filter", 0)
    project_rows = per_op.get("project", 0)
    join_rows = per_op.get("join", 0)
    agg_rows = per_op.get("aggregate", 0)
    sink_rows = sunk

    valid = (not cycles) and (len(topo) == len(ops))

    return [
        ("DAG_NODES", nodes_count),
        ("DAG_EDGES", edges_count),
        ("DAG_CYCLES", cycles),
        ("DAG_TOPSORT", topo),
        ("DAG_BREAKERS", breakers_list),
        ("DAG_FRAGMENTS", fragments_count),
        ("DAG_MORSEL_SIZE", MS),
        ("DAG_TICKS", ticks),
        ("DAG_ROWS_SCAN", scan1_rows + scan2_rows),
        ("DAG_ROWS_FILTERED", filter_rows),
        ("DAG_ROWS_PROJECTED", project_rows),
        ("DAG_ROWS_JOINED", join_rows),
        ("DAG_ROWS_AGGREGATED", agg_rows),
        ("DAG_ROWS_SUNK", sink_rows),
        ("PLAN_VALID", valid),
    ]

# ---------- main.aura ----------
def main():
    # Build the canned logical plan with 6 operators + an extra scan.
    ops = [
        op_make("scan1", "scan", []),
        op_make("filter", "filter", ["scan1"]),
        op_make("project", "project", ["filter"]),
        op_make("scan2", "scan", []),
        op_make("join", "join", ["project", "scan2"]),
        op_make("aggregate", "aggregate", ["join"]),
        op_make("sink", "sink", ["aggregate"]),
    ]
    edges = [
        ("scan1", "filter"),
        ("filter", "project"),
        ("project", "join"),
        ("scan2", "join"),
        ("join", "aggregate"),
        ("aggregate", "sink"),
    ]
    plan = plan_build(ops, edges)

    # Morsel size constant
    MS = morsel_size()

    # Run executor
    result = exec_run(plan, MS)

    # Build fragments for reporting (use ops' name list for topo)
    topo = toposort(ops, edges)
    breakers_named = set(op_name(o) for o in ops if breaker(op_kind(o)))
    frags = fragment_build(topo, breakers_named)

    # Format report
    lines = report_format(result, plan, frags)

    # Print KEY=value lines
    for k, v in lines:
        print(f"{k}={v}")

if __name__ == "__main__":
    main()
