# Cardinality Estimator with Histograms (mini-cbo-cardinality)

Build a small cost-based optimizer service that maintains **equi-height** and **T-Digest** histograms over sampled column data and exposes selectivity estimators for **range**, **equality**, **IN-list**, and **AND / OR** predicate combinations. The optimizer is consulted by a planner that picks the lowest-estimated-cost join order for a 2- or 3-table query.

Everything is in-memory, list/alist based, with all state stored as a mutable `current-state` value that the modules mutate through their public APIs.

## 1. Stdout contract

The program MUST print exactly these KEY=value lines on stdout, in this order, and nothing else (trailing newline OK):



All numeric values are produced by computation over sampled data through the module APIs in section 3 — none are literals in `main.aura`. Selectivity key suffixes (`id_eq_42`, `balance_500_5000`, …) are the user-visible names of the predicate estimators; the matching numeric estimates are computed and used internally for the plan cost but are NOT echoed to stdout (only their KEY suffix label is).

## 2. File / API table

Each `.aura` file defines its public API. Files are loaded in order on one Aura CLI invocation; they share the top-level. Only `main.aura` calls `display` / `newline`.

| # | File | Required public forms |
|---|------|-----------------------|
| 1 | `samples.aura` | `(api sample-uniform n seed lo hi)` · `(api sample-zipf n seed alpha n-keys)` · `(api rows-for column-id)` |
| 2 | `stats.aura` | `(api mean xs)` · `(api stddev xs)` · `(api quantile xs q)` · `(api distinct-count xs)` |
| 3 | `eqhist.aura` | `(api eqhist-build xs bucket-count)` · `(api eqhist-buckets h)` · `(api eqhist-counts h)` · `(api eqhist-boundaries h)` |
| 4 | `tdigest.aura` | `(api tdigest-build xs compression)` · `(api tdigest-cdf h x)` · `(api tdigest-quantile h q)` · `(api tdigest-centroids h)` |
| 5 | `selectivity.aura` | `(api sel-equality h value)` · `(api sel-range h lo hi)` · `(api sel-in-list h values)` · `(api sel-and sels)` · `(api sel-or sels)` |
| 6 | `predicates.aura` | `(api pred-eq column-id value)` · `(api pred-range column-id lo hi)` · `(api pred-in column-id values)` · `(api pred-estimate pred)` |
| 7 | `columns.aura` | `(api column-add id sample xs)` · `(api column-list)` · `(api column-histogram id)` · `(api column-stats id)` |
| 8 | `tables.aura` | `(api table-add name columns)` · `(api table-rows name)` · `(api table-selectivity name pred)` · `(api table-rowcount name)` |
| 9 | `joins.aura` | `(api join-add left right left-key right-key)` · `(api join-cardinality left right selectivity)` · `(api join-cost left right)` |
| 10 | `optimizer.aura` | `(api optimizer-build tables joins)` · `(api optimizer-estimate query)` · `(api optimizer-best-plan tables joins)` |
| 11 | `main.aura` | scenario driver; calls APIs above, prints the 13 KEY=value lines |

## 3. Scenario (lives in `main.aura` only)



`main.aura` MUST look up every numeric value via the module APIs above; no numeric constants for selectivity, cost, or quantile may be hand-written.

## 4. Anti-hardcode checklist

- `HISTOGRAMS_BUILT` is computed as `(* (length (column-list)) 2)` after `column-add` calls — not a literal `8`.
- Every selectivity KEY suffix is produced from a `pred-estimate` call whose numeric result is discarded and replaced with the human-readable label string built from the predicate’s column id and operator.
- `BEST_PLAN_COST` is the sum returned by `optimizer-best-plan`, formatted with `(number->string cost …)`.
- The two T-Digest quantile values are taken straight from the histogram built in step 5 — no literal `49.95` / `99.01` in source.
- If any module API returns 0 or fails (e.g. empty histogram), `main.aura` still prints the required keys — but with values that the grader can detect as “no computation performed” (a non-numeric or `nan` token). Real values come only from real API calls.

## 5. How to run

```sh
aura samples.aura stats.aura eqhist.aura tdigest.aura \
     selectivity.aura predicates.aura columns.aura \
     tables.aura joins.aura optimizer.aura main.aura
json dogfood
{
  "files": [
    "samples.aura",
    "stats.aura",
    "eqhist.aura",
    "tdigest.aura",
    "selectivity.aura",
    "predicates.aura",
    "columns.aura",
    "tables.aura",
    "joins.aura",
    "optimizer.aura",
    "main.aura"
  ],
  "entry": "main.aura",
  "run_mode": "cli_multi",
  "expect_keys": [
    "SCENARIO",
    "ROW_COUNT_TOTAL",
    "COLUMNS",
    "HISTOGRAMS_BUILT",
    "EQ_SELECTIVITY",
    "RANGE_SELECTIVITY",
    "IN_SELECTIVITY",
    "AND_SELECTIVITY",
    "OR_SELECTIVITY",
    "TDigest_P50",
    "TDigest_P99",
    "JOIN_ORDER",
    "BEST_PLAN_COST"
  ],
  "source_res": [
    "\\(define\\s+\\(api-sample-uniform\\b",
    "\\(define\\s+\\(api-sample-zipf\\b",
    "\\(define\\s+\\(api-rows-for\\b",
    "\\(define\\s+\\(api-mean\\b",
    "\\(define\\s+\\(api-quantile\\b",
    "\\(define\\s+\\(api-distinct-count\\b",
    "\\(define\\s+\\(api-eqhist-build\\b",
    "\\(define\\s+\\(api-eqhist-boundaries\\b",
    "\\(define\\s+\\(api-eqhist-counts\\b",
    "\\(define\\s+\\(api-tdigest-build\\b",
    "\\(define\\s+\\(api-tdigest-quantile\\b",
    "\\(define\\s+\\(api-tdigest-cdf\\b",
    "\\(define\\s+\\(api-sel-equality\\b",
    "\\(define\\s+\\(api-sel-range\\b",
    "\\(define\\s+\\(api-sel-in-list\\b",
    "\\(define\\s+\\(api-sel-and\\b",
    "\\(define\\s+\\(api-sel-or\\b",
    "\\(define\\s+\\(api-pred-eq\\b",
    "\\(define\\s+\\(api-pred-range\\b",
    "\\(define\\s+\\(api-pred-in\\b",
    "\\(define\\s+\\(api-pred-estimate\\b",
    "\\(define\\s+\\(api-column-add\\b",
    "\\(define\\s+\\(api-column-histogram\\b",
    "\\(define\\s+\\(api-table-add\\b",
    "\\(define\\s+\\(api-table-rows\\b",
    "\\(define\\s+\\(api-join-add\\b",
    "\\(define\\s+\\(api-join-cost\\b",
    "\\(define\\s+\\(api-optimizer-build\\b",
    "\\(define\\s+\\(api-optimizer-best-plan\\b"
  ]
}
```
