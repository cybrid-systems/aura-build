# GOAL.md — mini-cbo-stats

## Overview
A miniature **cost-based optimizer statistics** subsystem. It builds an **equi-depth histogram** over a column, a **reservoir-style sampled sketch**, and combines them into a **selectivity estimator**. A toy **join-order optimizer** consults the estimator to pick the cheaper join order between two tables (small loop vs. nested). All persistence is in-memory lists/alists; no I/O, no FFI.

## Exact stdout contract
The scenario must print exactly these `KEY=value` lines, in this order, one per line:



(14 keys total. `EQD_BUCKET_BOUNDS`, `SAMPLE_FIRST_5` are printed by `(display …)` so they render as parenthesized lists.)

## Module table
| File | Required exported `(define (api …))` forms |
|---|---|
| `hist.aura` | `(make-equi-depth column n-buckets)` → `(values bounds counts)`; `(bucket-bound bounds i)`; `(bucket-count counts i)`; `(n-buckets bounds)` |
| `sketch.aura` | `(make-reservoir k)` → state; `(reservoir-add! state v)`; `(reservoir-sample state)` |
| `card.aura` | `(approx-cardinality state)` (HyperLogLog-lite via reservoir-size based estimator); `(approx-distinct sample)` |
| `select.aura` | `(eq-selectivity bounds counts value)` (linear-interp inside bucket); `(range-selectivity bounds counts lo hi)` |
| `cost.aura` | `(small-loop-cost rows-A rows-B)`; `(nested-loop-cost rows-A rows-B)` |
| `joinopt.aura` | `(pick-driver rows-A rows-B)` → `'A` or `'B` |
| `data.aura` | `(make-column seed n)`; `(column-ref col i)`; `(column-length col)`; `(seed-dataset)` |
| `main.aura` | scenario driver — calls APIs only, then prints the 14 KEY=value lines |

(`hist` + `sketch` + `card` together ≈ 1 file each kept split for clarity; total `.aura` files = 8 minimum, up to 13 by optionally splitting `hist` into `hist-bound.aura`/`hist-count.aura`, or `select` into `select-eq.aura`/`select-range.aura`, or adding `hll.aura`, `rng.aura`, `pretty.aura`. The 13-file target is met by splitting; 8-file compact layout is also valid.)

## Scenario steps (main.aura)
1. Build a 1000-row column via `(make-column 42 1000)` and compute `DISTINCT_KEYS` via `(approx-distinct (reservoir-sample sk))` and `COL_CARDINALITY` via `(approx-cardinality sk)`.
2. Equi-depth histogram with 4 buckets: store `EQD_BUCKETS`, `EQD_MIN`, `EQD_MAX`, and the rendered bounds list in `EQD_BUCKET_BOUNDS`.
3. Reservoir of size 32: store `RESERVOIR_SIZE`, and the first 5 sampled values in `SAMPLE_FIRST_5`.
4. Selectivity probes: `EQ_SELECTIVITY_50` = `(eq-selectivity … 50)`; `RANGE_SELECTIVITY_20_80` = `(range-selectivity … 20 80)`.
5. Optimizer: for a join of 9 000 × 7 000 rows, choose driver via `(pick-driver 9000 7000)` and emit `JOIN_TABLE_A` / `JOIN_TABLE_B` (the driver is the smaller, listed twice with swapped labels), `EST_OUTPUT_ROWS` (= 9000 × 7000 / 1000 × 1000 if normalized, here fixed value 63 000), and `EST_COST_SMALL_LOOP` / `EST_COST_NESTED` via `(small-loop-cost …)` and `(nested-loop-cost …)`.
6. All values printed with `(display)` + `(newline)`; main never hardcodes numeric literals for the computed keys — every number except the 14 sentinel field names must originate from an API call.

## Anti-hardcode guard
- `main.aura` must (a) build the column with `(make-column …)`, (b) call `(make-equi-depth …)` and read bucket bounds via `(bucket-bound … i)` in a loop, (c) call `(reservoir-sample …)` and take the first five by `car`/`cdr` recursion, (d) call `(eq-selectivity …)` and `(range-selectivity …)`, and (e) call `(pick-driver …)` / `(cost …)` to obtain the join keys. A reviewer who stubs any of those APIs to return a constant must observe numeric drift, so the values cannot be reproduced by static `display` lines alone.

## How to run
```sh
aura hist.aura sketch.aura card.aura select.aura cost.aura joinopt.aura data.aura main.aura
json dogfood
{
  "files": [
    "hist.aura",
    "sketch.aura",
    "card.aura",
    "select.aura",
    "cost.aura",
    "joinopt.aura",
    "data.aura",
    "main.aura"
  ],
  "entry": "main.aura",
  "run_mode": "cli_multi",
  "expect_keys": [
    "EQD_BUCKETS",
    "EQD_MIN",
    "EQD_MAX",
    "EQD_BUCKET_BOUNDS",
    "RESERVOIR_SIZE",
    "SAMPLE_FIRST_5",
    "COL_CARDINALITY",
    "DISTINCT_KEYS",
    "EQ_SELECTIVITY_50",
    "RANGE_SELECTIVITY_20_80",
    "JOIN_TABLE_A",
    "JOIN_TABLE_B",
    "CHOSEN_DRIVER",
    "EST_OUTPUT_ROWS",
    "EST_COST_SMALL_LOOP",
    "EST_COST_NESTED"
  ],
  "source_res": [
    "\\(define\\s+\\(make-equi-depth\\b",
    "\\(define\\s+\\(bucket-bound\\b",
    "\\(define\\s+\\(bucket-count\\b",
    "\\(define\\s+\\(n-buckets\\b",
    "\\(define\\s+\\(make-reservoir\\b",
    "\\(define\\s+\\(reservoir-add!\\b",
    "\\(define\\s+\\(reservoir-sample\\b",
    "\\(define\\s+\\(approx-cardinality\\b",
    "\\(define\\s+\\(approx-distinct\\b",
    "\\(define\\s+\\(eq-selectivity\\b",
    "\\(define\\s+\\(range-selectivity\\b",
    "\\(define\\s+\\(small-loop-cost\\b",
    "\\(define\\s+\\(nested-loop-cost\\b",
    "\\(define\\s+\\(pick-driver\\b",
    "\\(define\\s+\\(make-column\\b",
    "\\(define\\s+\\(column-ref\\b",
    "\\(define\\s+\\(column-length\\b",
    "\\(define\\s+\\(seed-dataset\\b"
  ]
}
```
