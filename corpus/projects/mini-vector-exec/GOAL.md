# mini-vector-exec — Vectorized Volcano Executor

A tiny query-engine-style pipeline in Aura implementing a pull-based iterator model with batch-friendly operators (scan, filter, project, aggregate), runtime-adaptive batch sizing, and selective late materialization. Operators are wired into a Volcano-style tree; the root opens each batch on demand so memory stays bounded, and a batch governor tunes batch size from observed row widths.

## 1. Stdout contract

The scenario prints exactly these `KEY=value` lines, in this order, one per line:



## 2. Module table

All files are `.aura`, loaded in order on a single Aura CLI invocation. `main.aura` is last and prints the contract.

| File | Required `(define (api …))` forms |
|---|---|
| `config.aura` | `(api config-batch-min)`, `(api config-batch-max)`, `(api config-batch-init)`, `(api config-mode)` |
| `types.aura` | `(api make-batch)`, `(api batch-add-row!)`, `(api batch-rows)`, `(api batch-width)`, `(api batch-empty?)` |
| `schema.aura` | `(api schema-cols)`, `(api schema-col-index)`, `(api schema-late-cols)` |
| `source.aura` | `(api source-row-count)`, `(api source-row)`, `(api source-cols)` |
| `scan.aura` | `(api make-scan)`, `(api scan-open)`, `(api scan-next)`, `(api scan-close)` |
| `filter.aura` | `(api make-filter)`, `(api filter-open)`, `(api filter-next)`, `(api filter-close)` |
| `project.aura` | `(api make-project)`, `(api project-open)`, `(api project-next)`, `(api project-close)` |
| `aggregate.aura` | `(api make-aggregate)`, `(api aggregate-open)`, `(api aggregate-next)`, `(api aggregate-close)` |
| `merge.aura` | `(api make-merge)`, `(api merge-open)`, `(api merge-next)`, `(api merge-close)` |
| `late.aura` | `(api late-needed?)`, `(api late-emit)`, `(api late-project-others)` |
| `governor.aura` | `(api gov-init)`, `(api gov-observe!)`, `(api gov-batch-size)`, `(api gov-mode)` |
| `pipeline.aura` | `(api pipeline-stage-names)`, `(api pipeline-run-stats)`, `(api pipeline-execute)` |
| `main.aura` | `(api main-run)` |

## 3. Scenario steps (`main.aura` only prints after computing via APIs)

1. Load config via `config-batch-min`, `config-batch-max`, `config-batch-init`, `config-mode`; stash as global `*gov-min*`, `*gov-max*`, `*gov-init*`, `*mode*`.
2. Init governor with `(gov-init *gov-init* *gov-min* *gov-max*)`.
3. Build scan operator over `source-row-count` rows of width = `(length (schema-cols))`; collect scanned rows count into `rows-scanned`.
4. Wrap scan in filter operator (`colA > 50`); accumulate `rows-after-filter`.
5. Wrap in project operator that emits `(colB colA colD)`; track `rows-projected` and tag `late-needed?` for `colC`.
6. Wrap in aggregate operator that groups by `colB` and computes `count`; track `rows-aggregated`.
7. Merge two such pipelines (even/odd `id`) using the merge operator.
8. Open root with `pipeline-execute`; for each `pipeline-next`, call `gov-observe!` on the batch width then yield via `late-emit`.
9. Build `pipeline-stage-names` from `'(SCAN FILTER PROJECT AGGREGATE MERGE)` and print stages one per line under `STAGE=`.
10. Print `BATCH_GOV=ADAPTIVE`; print min/init/max from config getters; `LATE_MAT=colC` from `schema-late-cols`.
11. Print `ROWS_SCANNED/AFTER_FILTER/PROJECTED/AGGREGATED` from accumulator counters maintained during pull.
12. Print `EXEC_MODE=PULL` from `config-mode`; print `PHASE=DONE` last.

## 4. Anti-hardcode

`main.aura` must call into every module API listed above. Specifically:
- Every `ROWS_*` value is read from pipeline accumulators populated by `pipeline-run-stats`, which in turn counts batches produced by `scan-next`, `filter-next`, `project-next`, `aggregate-next`, `merge-next`.
- `BATCH_GOV_MIN/MAX/INIT` come from `config-batch-min/max/init`, not literals.
- `STAGE=` lines come from `pipeline-stage-names`, not a literal list.
- `LATE_MAT=colC` comes from the first symbol returned by `schema-late-cols`.
- `EXEC_MODE` comes from `config-mode`.

A run that prints the contract without invoking the operators, governor, and pipeline APIs is a hardcode and fails.

## 5. How to run



No external files, no network, no secrets. All data is synthesized in-memory by `source.aura` (10,000 deterministic rows over `colA, colB, colC, colD, id`).
