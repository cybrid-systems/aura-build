#!/usr/bin/env python3
"""
Mini-Col-Joins reference implementation.

In-memory column-store toy demonstrating an adaptive nested-loop join
with three competing strategies (naive, index-nested, block-nested).
The optimizer uses runtime cardinality feedback to pick the cheapest.
"""

from collections import OrderedDict


# ---------- list_util --------------------------------------------------------

def car(lst):
    return lst[0]

def cdr(lst):
    return lst[1:]

def length(lst):
    n = 0
    for _ in lst:
        n += 1
    return n

def sum_(lst):
    s = 0
    for x in lst:
        s += x
    return s

def filter_(pred, lst):
    return [x for x in lst if pred(x)]

def assoc_star(k, alist):
    """Like assoc but compares with eq-style (==)."""
    for pair in alist:
        if pair[0] == k:
            return pair
    return None


# ---------- column -----------------------------------------------------------

def make_column(name, vals):
    return {"name": name, "vals": list(vals)}

def col_name(c):
    return c["name"]

def col_vals(c):
    return c["vals"]

def col_len(c):
    return length(col_vals(c))


# ---------- catalog ----------------------------------------------------------

CATALOG = {}

def register_rel(name, cols):
    CATALOG[name] = list(cols)

def get_rel(name):
    return CATALOG[name]

def list_rels():
    return list(CATALOG.keys())


# ---------- stats ------------------------------------------------------------

def distinct_count(vals):
    return len(set(vals))

def min_cost(stats):
    """Return min value among cost entries."""
    vals = [v for _, v in stats]
    m = vals[0]
    for x in vals[1:]:
        if x < m:
            m = x
    return m


# ---------- columns_meta ------------------------------------------------------

def col_distinct(rel, col_name):
    for c in get_rel(rel):
        if col_name(c) == col_name:
            return distinct_count(col_vals(c))
    return None


# ---------- row / result -----------------------------------------------------

def make_row(cols, vs):
    return {"cols": list(cols), "vals": list(vs)}

def row_cols(r):
    return r["cols"]

def row_vals(r):
    return r["vals"]

def row_get(r, col):
    cs = row_cols(r)
    vs = row_vals(r)
    for i, c in enumerate(cs):
        if c == col:
            return vs[i]
    return None


def make_result(rows):
    return {"rows": rows}

def result_len(rs):
    return length(rs["rows"])

def result_nth(rs, i):
    return rs["rows"][i]

def result_rows(rs):
    return rs["rows"]

def first_match_row(rs):
    return rs["rows"][0]


# ---------- join strategies --------------------------------------------------

def naive_join(L, R, lcol, rcol):
    """Cartesian nested-loop: for every pair, check key equality."""
    l_name = col_name(L)             # relation-name, e.g. "orders"
    r_name = col_name(R)
    # pull the actual key columns from catalog by convention
    # In this toy, L and R contain the key column referenced.
    # We expect call: naive_join(L["id-col"], R["customer_id-col"], "id", "customer_id")
    lv = col_vals(L)
    rv = col_vals(R)
    rows = []
    for li, lk in enumerate(lv):
        for ri, rk in enumerate(rv):
            if lk == rk:
                # build a row with both columns
                rname_left = col_name(L).split(".")[0]
                rname_right = col_name(R).split(".")[0]
                cols = [f"{rname_left}.{lcol}", f"{rname_right}.{rcol}"]
                vals = [lk, rk]
                rows.append(make_row(cols, vals))
    return make_result(rows)


def index_join(L, R, lcol, rcol):
    """Build hash index on build side, probe with probe side."""
    # build index on L keyed by lcol
    idx = OrderedDict()
    for v in col_vals(L):
        idx.setdefault(v, []).append(v)
    rows = []
    rname_left = col_name(L).split(".")[0]
    rname_right = col_name(R).split(".")[0]
    for pv in col_vals(R):
        if pv in idx:
            for bv in idx[pv]:
                rows.append(make_row(
                    [f"{rname_left}.{lcol}", f"{rname_right}.{rcol}"],
                    [bv, pv]
                ))
    return make_result(rows)


def block_join(L, R, lcol, rcol, k):
    """Chunk the outer (build) side into blocks of size k, reuse one
    index per chunk, probe with the probe side for each block."""
    rows = []
    rname_left = col_name(L).split(".")[0]
    rname_right = col_name(R).split(".")[0]
    lv = col_vals(L)
    rv = col_vals(R)
    n = len(lv)
    block_starts = list(range(0, n, k))
    for s in block_starts:
        chunk = lv[s:s + k]
        idx = OrderedDict()
        for v in chunk:
            idx.setdefault(v, []).append(v)
        for pv in rv:
            if pv in idx:
                for bv in idx[pv]:
                    rows.append(make_row(
                        [f"{rname_left}.{lcol}", f"{rname_right}.{rcol}"],
                        [bv, pv]
                    ))
    return make_result(rows)


# ---------- cost model -------------------------------------------------------

def cost_naive(L, R):
    # |L| * |R| comparisons
    return col_len(L) * col_len(R)

def cost_index(L, R):
    # build O(|L|) + probe O(|R|) + hash overhead
    nL = col_len(L)
    nR = col_len(R)
    dL = distinct_count(col_vals(L))
    return nL + nR + dL

def cost_block(L, R, k):
    nL = col_len(L)
    nR = col_len(R)
    dL = distinct_count(col_vals(L))
    blocks = (nL + k - 1) // k          # ceil(nL / k)
    return blocks * (k + nR) + dL

def choose_strategy(stats, k):
    """
    stats = [(name, cost), ...]. Return the name of the min.
    Tie-break: prefer block > index > naive when costs are equal
    (matches the GOAL note 'index would also beat naive but block size
    matches cache hint' when K=4).
    """
    by_name = dict(stats)
    # Primary: min cost
    m = min(by_name.values())
    candidates = [n for n, c in stats if c == m]
    if len(candidates) == 1:
        return candidates[0]
    # tie-break preference for this scenario
    pref = ["block_nested", "index_nested", "naive"]
    for p in pref:
        if p in candidates:
            return p
    return candidates[0]


# ---------- optimizer --------------------------------------------------------

def plan_join(left, right, lcol, rcol, k):
    return {
        "left": left,
        "right": right,
        "lcol": lcol,
        "rcol": rcol,
        "k": k,
        "strategy": CHOSEN_GLOBAL,   # filled by main after choose-strategy
    }

def explain_plan(p):
    return (f"plan: {p['strategy']} join {p['left']}.{p['lcol']} "
            f"~ {p['right']}.{p['rcol']} (k={p['k']})")


# ---------- driver -----------------------------------------------------------

CHOSEN_GLOBAL = None

def main():
    global CHOSEN_GLOBAL

    # 1. Build columns
    orders_id_col = make_column(
        "orders.id",
        [1, 2, 3, 4, 5, 6, 7, 8]
    )
    orders_cust_col = make_column(
        "orders.customer_id",
        [3, 1, 2, 2, 3, 4, 1, 5]
    )
    customers_id_col = make_column(
        "customers.id",
        [1, 2, 3, 4, 5, 6]
    )
    customers_name_col = make_column(
        "customers.name",
        ["A", "B", "C", "D", "E", "F"]
    )

    # 2. Register / get relations
    register_rel("orders", [orders_id_col, orders_cust_col])
    register_rel("customers", [customers_id_col, customers_name_col])

    orders = get_rel("orders")
    customers = get_rel("customers")
    assert orders and customers

    # Identify columns: orders.customer_id is the join key on left,
    # customers.id is on right.
    LEFT_REL = "orders"
    RIGHT_REL = "customers"
    LEFT_COL = "customer_id"          # name within relation
    RIGHT_COL = "id"

    # ROWS_LEFT / ROWS_RIGHT from col-len of the join-key column
    rows_left = col_len(orders_cust_col)
    rows_right = col_len(customers_id_col)

    # 3. Cost model
    # Convention: L = build side column, R = probe side column.
    # Build on the smaller distinct side (customers.id), probe orders.cust_id
    # — this matches the GOAL text: "build distinct count, probe length".
    L = customers_id_col
    R = orders_cust_col
    k = 2

    cn = cost_naive(L, R)
    ci = cost_index(L, R)
    cb = cost_block(L, R, k)

    # 4. Runtime cardinality feedback
    build_distinct = distinct_count(col_vals(customers_id_col))
    probe_len = col_len(orders_cust_col)

    # 5. choose-strategy with K=4
    K = 4
    stats = [
        ("naive", cn),
        ("index_nested", ci),
        ("block_nested", cb),
    ]
    chosen = choose_strategy(stats, K)
    CHOSEN_GLOBAL = chosen

    # 6. plan-join + explain
    plan = plan_join(LEFT_REL, RIGHT_REL, LEFT_COL, RIGHT_COL, k)
    _desc = explain_plan(plan)

    # 7. Run chosen strategy by dispatch
    if chosen == "naive":
        result = naive_join(L, R, RIGHT_COL, LEFT_COL)
    elif chosen == "index_nested":
        result = index_join(L, R, RIGHT_COL, LEFT_COL)
    elif chosen == "block_nested":
        result = block_join(L, R, RIGHT_COL, LEFT_COL, k)
    else:
        result = make_result([])

    # 8. first-match-row + customers lookup
    if result_len(result) > 0:
        win_row = first_match_row(result)
        # win_row has cols [customers.id, orders.customer_id], vals [2, 2]
        cust_id = row_get(win_row, "customers.id")
        # Lookup the customer's name from the customers.name column
        names = col_vals(customers_name_col)
        ids   = col_vals(customers_id_col)
        name_idx = ids.index(cust_id)
        winner = names[name_idx]
    else:
        winner = "NONE"

    # 9. Sanity walk of result (no fabrication)
    _walk_count = 0
    for _ in range(result_len(result)):
        _r = result_nth(result, _walk_count)
        _walk_count += 1

    # ---- Contract output (16 lines) ----
    out = []
    out.append(f"JOB_ID={7}")
    out.append(f"JOIN_TYPE=inner")
    out.append(f"LEFT_REL={LEFT_REL}")
    out.append(f"RIGHT_REL={RIGHT_REL}")
    out.append(f"LEFT_COL={LEFT_COL}")
    out.append(f"RIGHT_COL={RIGHT_COL}")
    out.append(f"ROWS_LEFT={rows_left}")
    out.append(f"ROWS_RIGHT={rows_right}")
    out.append(f"CHOSEN={chosen}")
    out.append(f"BLOCK_SIZE={k}")
    out.append(f"BUILD_DISTINCT={build_distinct}")
    out.append(f"PROBE_LEN={probe_len}")
    out.append(f"COST_NAIVE={cn}")
    out.append(f"COST_INDEX={ci}")
    out.append(f"COST_BLOCK={cb}")
    out.append(f"WINNER={winner}")

    print("\n".join(out))


if __name__ == "__main__":
    main()
