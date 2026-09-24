# Zone-Map Pruning Stats — GOAL.md

## Overview
A tiny in-memory "columnar zone" engine that maintains per-zone min/max/null-count/distinct-value-count summaries (zone maps) over rows of records, supports dictionary encoding for low-cardinality strings, and applies automatic zone-map maintenance on inserts/deletes. A range query counts how many zones can be pruned without scanning their rows, and reports pruning statistics. Demonstrates classic storage-engine zone-map + dictionary encoding + segment pruning ideas in a single Aura CLI run.

## Stdout contract (KEY=value lines, in order)


## Module table

| File | Required `(define (api …))` forms |
|---|---|
| `values.aura` | `(api make-null)`, `(api null?)`, `(api null-value)`, `(api int-val)`, `(api str-val)`, `(api int->cell)`, `(api str->cell)`, `(api cell=? )`, `(api cell-print)` |
| `column.aura` | `(api make-column)`, `(api column-name)`, `(api column-type)`, `(api column-add!)`, `(api column-size)`, `(api column-ref)`, `(api col-min)`, `(api col-max)`, `(api col-nulls)`, `(api col-ndv)`, `(api column-recompute!)` |
| `dictionary.aura` | `(api dict-create)`, `(api dict-size)`, `(api dict-get-id)`, `(api dict-get-value)`, `(api dict-encode!)`, `(api dict-decode)` |
| `zone.aura` | `(api make-zone)`, `(api zone-rows)`, `(api zone-stat)`, `(api zone-refresh!)`, `(api zone-matches?)`, `(api zone-row-ref)` |
| `zonemap.aura` | `(api make-zonemap)`, `(api zonemap-add-zone!)`, `(api zonemap-zones)`, `(api zonemap-get-zone)`, `(api zonemap-prune-stats)`, `(api zonemap-prune-range)`, `(api zonemap-row-count)`, `(api zonemap-flatten-row)` |
| `table.aura` | `(api make-table)`, `(api table-add-column!)`, `(api table-append-row!)`, `(api table-delete-row!)`, `(api table-row-count)`, `(api table-zonemap)`, `(api table-maintain!)` |
| `pruner.aura` | `(api pruner-stats)`, `(api pruner-execute)`, `(api pruner-ratio)`, `(api pruner-scanned)` |
| `rng.aura` | `(api make-rng)`, `(api rng-next)`, `(api rng-int)`, `(api rng-string)`, `(api rng-shuffle)` |
| `driver.aura` | `(api build-dataset)`, `(api run-range-query)`, `(api collect-stats)`, `(api stats-lines)` |
| `main.aura` | (entry point; orchestrates `driver`, prints 14 KEY=value lines) |

## Scenario steps (executed in `main.aura`)
1. Build an RNG with deterministic seed.
2. Call `driver:build-dataset` to create a table with columns `col-a` (int) and `col-b` (low-cardinality string), then `table:table-maintain!` to refresh zones and dictionary.
3. Run a range query `(col-a BETWEEN lo AND hi)` via `driver:run-range-query` returning pruned/scanned/result counts.
4. Walk the zonemap and gather per-column zone-min/max/null-count/ndv via `column:col-min`, `column:col-max`, `column:col-nulls`, `column:col-ndv`.
5. Pull dictionary size for `col-b` using `dictionary:dict-size`.
6. Emit all 14 KEY=value lines via `(display …) (newline)`.

## Anti-hardcode
- `main.aura` MUST call `driver:build-dataset`, `table:table-maintain!`, `driver:run-range-query`, `driver:collect-stats`, and the column/dictionary APIs to compute every printed value.
- Forbidden: directly `(display "RESULT_ROWS=…")` style literals. Every value printed must originate from a module API result.

## How to run
