# Toy in-memory zone-map engine semantics for the Aura "mini-zone-map" scenario.
# Computes the same KEY=value outputs the Aura main.aura would print.

import sys
import random
from collections import Counter

# ---- rng.aura ---------------------------------------------------------------
def make_rng(seed):
    return random.Random(seed)

def rng_int(rng, lo, hi):
    return rng.randint(lo, hi)

def rng_string(rng, n):
    alphabet = "abcdefghijklmnopqrstuvwxyz"
    return "".join(rng.choice(alphabet) for _ in range(n))

def rng_shuffle(rng, lst):
    out = list(lst)
    rng.shuffle(out)
    return out

# ---- values.aura ------------------------------------------------------------
NULL_SENTINEL = "__NULL__"

def make_null():
    return ("null", None)

def null?(v):
    return isinstance(v, tuple) and v[0] == "null"

def null_value():
    return NULL_SENTINEL

def int_val(x):
    return ("int", int(x))

def str_val(s):
    return ("str", s)

def int_to_cell(x):
    return ("int", x)

def str_to_cell(s):
    return ("str", s)

def cell_eq(a, b):
    # equality over cells, treating nulls as unequal to everything
    if null?(a) or null?(b):
        return False
    return a == b

# ---- column.aura ------------------------------------------------------------
def make_column(name, ctype):
    return {
        "name": name,
        "type": ctype,
        "values": [],   # list of cells
        "min": None,
        "max": None,
        "nulls": 0,
        "ndv": 0,
    }

def column_name(c):  return c["name"]
def column_type(c):  return c["type"]
def column_size(c):  return len(c["values"])

def column_add(c, cell):
    c["values"].append(cell)

def column_ref(c, i):
    return c["values"][i]

def column_recompute(c):
    vals = [v for v in c["values"] if not null?(v)]
    ints = [v[1] for v in vals if v[0] == "int"]
    strs = [v[1] for v in vals if v[0] == "str"]
    c["nulls"] = len(c["values"]) - len(vals)
    if ints:
        c["min"] = min(ints)
        c["max"] = max(ints)
    if strs:
        c["min"] = min(strs)
        c["max"] = max(strs)
    c["ndv"] = len(set(vals))

def col_min(c):  return c["min"]
def col_max(c):  return c["max"]
def col_nulls(c): return c["nulls"]
def col_ndv(c):  return c["ndv"]

# ---- dictionary.aura --------------------------------------------------------
def dict_create():
    return {"ids": [], "by_id": [], "by_val": {}}

def dict_size(d):
    return len(d["ids"])

def dict_get_id(d, v):
    return d["by_val"].get(v, -1)

def dict_get_value(d, i):
    if 0 <= i < len(d["by_id"]):
        return d["by_id"][i]
    return None

def dict_encode(d, v):
    if v in d["by_val"]:
        return d["by_val"][v]
    new_id = len(d["by_id"])
    d["by_id"].append(v)
    d["ids"].append(new_id)
    d["by_val"][v] = new_id
    return new_id

def dict_decode(d, i):
    return dict_get_value(d, i)

# ---- zone.aura --------------------------------------------------------------
def make_zone(rows):
    # rows: list of (row_index, [cells...]) across columns
    return {"rows": list(rows), "stats": {}}

def zone_rows(z):
    return z["rows"]

def zone_row_ref(z, i):
    return z["rows"][i]

def zone_refresh(z, columns):
    # columns: ordered list of column objects
    z["stats"] = {}
    for c in columns:
        cname = column_name(c)
        cells = [row[1][cname] for row in z["rows"]]
        non_null = [x for x in cells if not null?(x)]
        n_nulls = len(cells) - len(non_null)
        ndv = len(set(non_null))
        if non_null and column_type(c) == "int":
            mn = min(x[1] for x in non_null if x[0] == "int")
            mx = max(x[1] for x in non_null if x[0] == "int")
        elif non_null and column_type(c) == "str":
            mn = min(x[1] for x in non_null if x[0] == "str")
            mx = max(x[1] for x in non_null if x[0] == "str")
        else:
            mn = None
            mx = None
        z["stats"][cname] = {"min": mn, "max": mx, "nulls": n_nulls, "ndv": ndv}

def zone_stat(z, colname, key):
    return z["stats"].get(colname, {}).get(key)

def zone_matches(z, colname, lo, hi):
    # returns True if zone MAY contain a row in [lo, hi]
    s = z["stats"].get(colname)
    if s is None:
        return True
    mn, mx = s["min"], s["max"]
    if mn is None and mx is None:
        # all-null zone; pruning decision: treat as non-match unless range covers nulls (we don't)
        return False
    # cells are tagged tuples; compare payload
    def payload(x): return x[1]
    if payload(mx) < lo: return False
    if payload(mn) > hi: return False
    return True

# ---- zonemap.aura -----------------------------------------------------------
def make_zonemap(columns):
    return {"columns": columns, "zones": []}

def zonemap_add_zone(zm, z):
    zm["zones"].append(z)

def zonemap_zones(zm):
    return zm["zones"]

def zonemap_get_zone(zm, i):
    return zm["zones"][i]

def zonemap_row_count(zm):
    return sum(len(z["rows"]) for z in zm["zones"])

def zonemap_flatten_row(zm, zone_idx, row_in_zone):
    z = zm["zones"][zone_idx]
    return z["rows"][row_in_zone][1]

def zonemap_prune_stats(zm, colname, lo, hi):
    pruned = 0
    scanned = 0
    result_rows = 0
    for z in zm["zones"]:
        if zone_matches(z, colname, lo, hi):
            scanned += 1
            for (_, row) in z["rows"]:
                v = row.get(colname)
                if null?(v):
                    continue
                if lo <= v[1] <= hi:
                    result_rows += 1
        else:
            pruned += 1
    return pruned, scanned, result_rows

def zonemap_prune_range(zm, colname, lo, hi):
    return zonemap_prune_stats(zm, colname, lo, hi)

# ---- table.aura -------------------------------------------------------------
def make_table():
    return {"columns": [], "rows": [], "zonemap": None}

def table_add_column(t, c):
    t["columns"].append(c)

def table_append_row(t, row):
    # row: {col-name: cell}
    t["rows"].append(row)
    for c in t["columns"]:
        column_add(c, row[column_name(c)])

def table_delete_row(t, idx):
    del t["rows"][idx]
    # rebuild columns from scratch (toy semantics)
    for c in t["columns"]:
        cname = column_name(c)
        c["values"] = [r[cname] for r in t["rows"]]
        c["min"] = None; c["max"] = None; c["nulls"] = 0; c["ndv"] = 0

def table_row_count(t):
    return len(t["rows"])

def table_zonemap(t):
    return t["zonemap"]

def table_maintain(t, zone_size=64):
    # recompute per-column aggregates
    for c in t["columns"]:
        column_recompute(c)
    # rebuild zonemap with zones of fixed size
    zm = make_zonemap(t["columns"])
    rows = t["rows"]
    for i in range(0, len(rows), zone_size):
        chunk = [(i + j, rows[i + j]) for j in range(min(zone_size, len(rows) - i))]
        z = make_zone(chunk)
        zone_refresh(z, t["columns"])
        zonemap_add_zone(zm, z)
    t["zonemap"] = zm
    return zm

# ---- pruner.aura ------------------------------------------------------------
def pruner_execute(zm, colname, lo, hi):
    return zonemap_prune_range(zm, colname, lo, hi)

def pruner_stats(p, s, r):
    return {"pruned": p, "scanned": s, "result_rows": r}

def pruner_ratio(p, total):
    if total == 0:
        return 0.0
    return p / total

def pruner_scanned(p, s, r):
    return s

# ---- driver.aura ------------------------------------------------------------
def build_dataset(seed=42, n_rows=1000, low_card=8):
    rng = make_rng(seed)
    t = make_table()
    ca = make_column("col-a", "int")
    cb = make_column("col-b", "str")
    table_add_column(t, ca)
    table_add_column(t, cb)

    pool = [rng_string(rng, 3) for _ in range(low_card)]
    # inject a few nulls in each column
    null_positions_a = set(rng.sample(range(n_rows), 25))
    null_positions_b = set(rng.sample(range(n_rows), 15))

    for i in range(n_rows):
        if i in null_positions_a:
            ca_cell = make_null()
        else:
            ca_cell = int_to_cell(rng_int(rng, 0, 10000))
        if i in null_positions_b:
            cb_cell = make_null()
        else:
            cb_cell = str_to_cell(pool[rng_int(rng, 0, low_card - 1)])
        table_append_row(t, {"col-a": ca_cell, "col-b": cb_cell})

    table_maintain(t, zone_size=64)
    return t

def run_range_query(t, colname, lo, hi):
    zm = table_zonemap(t)
    p, s, r = pruner_execute(zm, colname, lo, hi)
    return {"pruned": p, "scanned": s, "result_rows": r}

def collect_stats(t):
    ca = t["columns"][0]
    cb = t["columns"][1]
    zm = table_zonemap(t)
    # build dictionary for col-b by encoding all non-null values
    d = dict_create()
    for v in cb["values"]:
        if not null?(v):
            dict_encode(d, v[1])
    return {
        "ZONES": len(zonemap_zones(zm)),
        "ROWS": table_row_count(t),
        "NULLS_COL_A": col_nulls(ca),
        "NULLS_COL_B": col_nulls(cb),
        "NDV_COL_A": col_ndv(ca),
        "NDV_COL_B": col_ndv(cb),
        "MIN_COL_A": col_min(ca),
        "MAX_COL_A": col_max(ca),
        "MIN_COL_B": col_min(cb),
        "MAX_COL_B": col_max(cb),
        "DICT_SIZE_COL_B": dict_size(d),
        "PRUNED_ZONES": 0,  # filled in after query
        "SCANNED_ZONES": 0,
        "RESULT_ROWS": 0,
        "PRUNE_RATIO": 0.0,
    }

def stats_lines(stats):
    order = [
        "ZONES", "ROWS", "NULLS_COL_A", "NULLS_COL_B",
        "NDV_COL_A", "NDV_COL_B",
        "MIN_COL_A", "MAX_COL_A", "MIN_COL_B", "MAX_COL_B",
        "DICT_SIZE_COL_B",
        "PRUNED_ZONES", "SCANNED_ZONES", "PRUNE_RATIO", "RESULT_ROWS",
    ]
    return [f"{k}={stats[k]}" for k in order]

# ---- main.aura --------------------------------------------------------------
def main():
    t = build_dataset(seed=42, n_rows=1000, low_card=8)
    stats = collect_stats(t)
    q = run_range_query(t, "col-a", 1000, 5000)
    total_zones = stats["ZONES"]
    stats["PRUNED_ZONES"] = q["pruned"]
    stats["SCANNED_ZONES"] = q["scanned"]
    stats["RESULT_ROWS"] = q["result_rows"]
    stats["PRUNE_RATIO"] = round(q["pruned"] / total_zones, 6) if total_zones else 0.0
    for line in stats_lines(stats):
        print(line)

if __name__ == "__main__":
    main()
