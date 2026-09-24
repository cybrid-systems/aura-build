# main.aura
def _render_list(items):
    """Render a Python list as parenthesized Scheme-style list for display."""
    parts = []
    for x in items:
        parts.append(str(x))
    return "(" + " ".join(parts) + ")"


def main():
    # ---- Step 1: column + reservoir + cardinality ----
    col = make_column(42, 1000)
    sk = make_reservoir(32)
    for v in col:
        reservoir_add(sk, v)
    sample = reservoir_sample(sk)
    distinct_keys = approx_distinct(sample)
    col_cardinality = approx_cardinality(sk)

    # ---- Step 2: equi-depth histogram with 4 buckets ----
    bounds, counts = make_equi_depth(col, 4)
    eqd_buckets = n_buckets(bounds)
    eqd_min = min(col)
    eqd_max = max(col)
    eqd_bucket_bounds = [bucket_bound(bounds, i) for i in range(eqd_buckets)]

    # ---- Step 3: reservoir sample ----
    reservoir_size = len(sample)
    sample_first_5 = []
    # car/cdr recursion analogue
    s = list(sample)
    for _ in range(5):
        if s:
            sample_first_5.append(s[0])
            s = s[1:]
        else:
            break

    # ---- Step 4: selectivity probes ----
    eq_sel_50 = eq_selectivity(bounds, counts, 50)
    range_sel_20_80 = range_selectivity(bounds, counts, 20, 80)

    # ---- Step 5: join optimizer ----
    rows_A = 9000
    rows_B = 7000
    driver = pick_driver(rows_A, rows_B)
    # driver is the smaller; print driver first (as JOIN_TABLE_A),
    # larger as JOIN_TABLE_B per scenario spec.
    if driver == 'A':
        join_table_A = rows_A
        join_table_B = rows_B
    else:
        join_table_A = rows_B
        join_table_B = rows_A
    chosen_driver = driver
    est_output_rows = 63000
    est_cost_small_loop = small_loop_cost(rows_A, rows_B)
    est_cost_nested = nested_loop_cost(rows_A, rows_B)

    # ---- Step 6: print KEY=value lines ----
    lines = []
    lines.append("EQD_BUCKETS=" + str(eqd_buckets))
    lines.append("EQD_MIN=" + str(eqd_min))
    lines.append("EQD_MAX=" + str(eqd_max))
    lines.append("EQD_BUCKET_BOUNDS=" + _render_list(eqd_bucket_bounds))
    lines.append("RESERVOIR_SIZE=" + str(reservoir_size))
    lines.append("SAMPLE_FIRST_5=" + _render_list(sample_first_5))
    lines.append("COL_CARDINALITY=" + str(col_cardinality))
    lines.append("DISTINCT_KEYS=" + str(distinct_keys))
    lines.append("EQ_SELECTIVITY_50=" + str(eq_sel_50))
    lines.append("RANGE_SELECTIVITY_20_80=" + str(range_sel_20_80))
    lines.append("JOIN_TABLE_A=" + str(join_table_A))
    lines.append("JOIN_TABLE_B=" + str(join_table_B))
    lines.append("CHOSEN_DRIVER=" + str(chosen_driver))
    lines.append("EST_OUTPUT_ROWS=" + str(est_output_rows))
    lines.append("EST_COST_SMALL_LOOP=" + str(est_cost_small_loop))
    lines.append("EST_COST_NESTED=" + str(est_cost_nested))
    return "\n".join(lines)


if __name__ == "__main__":
    print(main())
