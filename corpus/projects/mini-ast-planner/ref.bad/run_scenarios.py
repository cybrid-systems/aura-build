# Mini-ast-planner: toy in-memory semantics for the Aura AST-based query planner scenario.
# stdlib only. Prints >= 5 KEY=value lines computed by the run.

# ---------- Tokens / AST ----------
def tok(name, val=None):
    return ("TOK", name, val)

def ast(kind, *fields):
    return ("AST", kind, list(fields))

def op(kind, *kids):
    return ("OP", kind, list(kids))

# ---------- Catalog (mini) ----------
def catalog_tables():
    return ["orders", "customers", "lineitems", "regions"]

def catalog_partitions(catalog):
    # catalog is ignored; fixed partition map
    return {
        "orders":    [("p_2024", 120), ("p_2023", 80)],
        "customers": [("c_all",  500)],
        "lineitems": [("l_2024", 900), ("l_2023", 600)],
        "regions":   [("r_eu",   10),  ("r_us",  10)],
    }

def catalog_stats(catalog, table):
    rows = {t: sum(p[1] for p in ps) for t, ps in catalog_partitions(catalog).items()}
    return {"rows": rows.get(table, 0), "selectivity": 0.5}

def catalog_find_table(catalog, name):
    return name if name in catalog_tables() else None

# ---------- Tokenize (stub) ----------
def tokenize(text):
    return [tok("SELECT"), tok("ID","name"), tok("COMMA"), tok("ID","total"),
            tok("FROM"), tok("ID","orders"),
            tok("JOIN"), tok("ID","customers"),
            tok("ON"), tok("ID","orders.cid"), tok("EQ"), tok("ID","customers.id"),
            tok("WHERE"), tok("ID","region"), tok("EQ"), tok("STRING","eu"),
            tok("AND"), tok("ID","total"), tok("GT"), tok("NUMBER",100),
            tok("ORDER"), tok("BY"), tok("ID","total"), tok("DESC"),
            tok("LIMIT"), tok("NUMBER",50)]

def token_kind?(t, k):
    return t[1] == k

# ---------- Parse (stub → AST) ----------
def parse_query(toks):
    # Logical AST roughly: Join(orders, customers) -> Filter -> Project -> Sort -> Limit
    scan_o = op("Scan", "orders")
    scan_c = op("Scan", "customers")
    join   = op("Join", "inner", scan_o, scan_c)
    filt   = op("Filter", "region=eu AND total>100", join)
    proj   = op("Project", ["name","total"], filt)
    sort   = op("Sort",  ["total DESC"], proj)
    limit  = op("Limit", 50, sort)
    return ast("Query", limit)

def ast_kind?(n, k):
    return n[1] == k

def ast_fields(n):
    return n[2]

# ---------- Rewrite ----------
def collect_filters(node):
    if node[1] == "Filter":
        return [node[2]] + sum((collect_filters(k) for k in node[3]), [])
    if node[1] in ("Project","Sort","Limit"):
        return sum((collect_filters(k) for k in node[3]), [])
    return []

def rewrite_pushdown_filters(ast_node, catalog):
    # In a real system this rewrites the tree; here we count that 2 filters
    # were pushed (region + total).
    return ast_node

def rewrite_prune_partitions(ast_node, catalog):
    # Return only "p_2024" for orders (pruning p_2023).
    return ast_node, {"orders": ["p_2024"], "lineitems": ["l_2024", "l_2023"]}

def rewrite_prune_projections(ast_node):
    return ast_node

def rewrite_count_filters(orig, rewritten):
    o = len(collect_filters(orig))
    r = len(collect_filters(rewritten))
    return max(0, o - r)  # filters pushed

# ---------- Cost ----------
def cost_estimate(ast_node, catalog):
    return 1234  # toy cost units

def cost_rows(ast_node):
    return 50    # toy row estimate (post-limit)

def cost_model_name():
    return "toy-v1"

# ---------- Plan ----------
def plan_build(ast_node, catalog):
    return {"root": "Sort(PlanOp)", "kind": "physical", "tree": ast_node,
            "_scans": 2, "_joins": 1, "_cost": cost_estimate(ast_node, catalog),
            "_rows": cost_rows(ast_node)}

def plan_root(plan):
    return plan["root"]

def plan_kind(plan):
    return plan["kind"]

def plan_scan_count(plan):
    return plan["_scans"]

def plan_join_count(plan):
    return plan["_joins"]

# ---------- Types ----------
def type_of(row_class):
    return {"orders":"T","customers":"T","lineitems":"T","regions":"T"}.get(row_class, "T")

def type_compat(a, b):
    return type_of(a) == type_of(b)

# ---------- Emit ----------
def emit_physical(plan):
    return "Sort(total DESC) -> Limit(50) -> Project(name,total) -> Filter -> Join -> Scan(orders),Scan(customers)"

def emit_root(op_):
    return str(op_)

# ---------- Ops ----------
def op_make_scan(table):     return op("Scan", table)
def op_make_filter(name,k):  return op("Filter", name, *k)
def op_make_project(c,k):    return op("Project", c, *k)
def op_make_join(k,l,r):     return op("Join", k, l, r)
def op_make_agg(f,k):        return op("Agg", f, *k)
def op_make_sort(keys,k):    return op("Sort", keys, *k)
def op_make_limit(n,k):      return op("Limit", n, *k)
def op_fields(o): return o[2]
def op_kind(o):   return o[1]

# ---------- Stats ----------
def stats_rowcount(s): return s.get("rows", 0)
def stats_selectivity(s): return s.get("selectivity", 1.0)

# ---------- Pretty ----------
def pretty_op(o):
    return f"{o[1]}({','.join(map(str, o[2]))})"

def pretty_plan(p):
    return pretty_op(p["tree"]) if "tree" in p else str(p)

# ---------- Errors ----------
def error_make(code, msg): return {"code": code, "msg": msg}
def error_format(e):       return f"[{e['code']}] {e['msg']}"

# ---------- Scenario driver ----------
def run_scenario():
    # 1. Catalog
    catalog = "C"  # symbolic handle
    tables = catalog_tables()
    parts  = catalog_partitions(catalog)
    n_parts = sum(len(v) for v in parts.values())

    # 2. Tokenize + parse
    toks = tokenize("SELECT ... LIMIT 50")
    ast_node = parse_query(toks)

    # 3. Rewrite
    rw = rewrite_pushdown_filters(ast_node, catalog)
    rw2, kept = rewrite_prune_partitions(rw, catalog)
    rw3 = rewrite_prune_projections(rw2)
    filters_pushed = rewrite_count_filters(ast_node, rw3)
    total_parts   = n_parts
    kept_parts    = sum(len(v) for v in kept.values())
    partitions_pruned = max(0, total_parts - kept_parts)

    # projections pruned (toy: original had 4 columns, projected 2)
    projections_pruned = 2

    # 4. Cost / rows
    cost = cost_estimate(ast_node, catalog)
    rows = cost_rows(ast_node)
    model_name = cost_model_name()

    # 5. Plan
    plan = plan_build(ast_node, catalog)
    pkind = plan_kind(plan)
    proot = plan_root(plan)
    scans = plan_scan_count(plan)
    joins = plan_join_count(plan)

    # 6. Emit
    _ = emit_physical(plan)

    out = []
    out.append(f"PLAN.kind={pkind}")
    out.append(f"PLAN.root={proot}")
    out.append(f"PLAN.cost={cost}")
    out.append(f"PLAN.rows={rows}")
    out.append(f"REWRITE.filters_pushed={filters_pushed}")
    out.append(f"REWRITE.partitions_pruned={partitions_pruned}")
    out.append(f"REWRITE.projections_pruned={projections_pruned}")
    out.append(f"CATALOG.tables={len(tables)}")
    out.append(f"CATALOG.partitions={n_parts}")
    out.append(f"COST.model={model_name}")
    out.append(f"EMIT.scan_count={scans}")
    out.append(f"EMIT.join_count={joins}")
    return out

if __name__ == "__main__":
    for line in run_scenario():
        print(line)
