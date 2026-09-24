# Columnar CSV Scan Engine

A toy streaming columnar CSV scanner written in Aura (Lisp-like). Reads CSV records from in-memory data sources, projects requested columns, applies filter predicates (with simple predicate pushdown), accumulates min/max/sum/count aggregates per column, and reports per-column batch statistics. The scan is column-oriented: each batch is materialized as a per-column list of values rather than row tuples, mirroring how a real vectorized executor lays out data.

## Stdout contract

The scenario prints exactly these KEY=value lines, in this order:



Where `<name>` is one entry per projected column, in projection order. Values are integers or strings (`pushdown_predicates` is a comma-separated string, `projected_cols` is a comma-separated string, `status` is the literal `OK`).

## Module table

| File | Required API forms |
|------|--------------------|
| `types.aura` | `(define-record-column name values)`, `(define (col-name c) ...)`, `(define (col-values c) ...)`, `(define (make-batch cols rows) ...)`, `(define (batch-cols b) ...)`, `(define (batch-row-count b) ...)` |
| `datasource.aura` | `(define (make-rows-source header rows) ...)`, `(define (source-header s) ...)`, `(define (source-rows s) ...)`, `(define (source-row-count s) ...)` |
| `parser.aura` | `(define (parse-row header line) ...)`, `(define (parse-cell s) ...)`, `(define (is-null-cell? s) ...)`, `(define (cell->number s) ...)` |
| `projection.aura` | `(define (make-projection col-names) ...)`, `(define (projection-cols p) ...)`, `(define (project-batch b p) ...)`, `(define (project-source src p) ...)` |
| `predicates.aura` | `(define (make-predicate col op value) ...)`, `(define (predicate-col pred) ...)`, `(define (predicate-op pred) ...)`, `(define (predicate-value pred) ...)`, `(define (eval-predicate pred cell) ...)`, `(define (filter-batch b p pred) ...)` |
| `pushdown.aura` | `(define (extract-pushdown header preds) ...)`, `(define (pushdown-applicable? p) ...)`, `(define (apply-pushdown src p) ...)`, `(define (pushdown-count p) ...)` |
| `aggregates.aura` | `(define (make-aggregator cols) ...)`, `(define (aggregator-cols a) ...)`, `(define (agg-update! a col-name values) ...)`, `(define (agg-count a col-name) ...)`, `(define (agg-sum a col-name) ...)`, `(define (agg-min a col-name) ...)`, `(define (agg-max a col-name) ...)`, `(define (agg-nulls a col-name) ...)` |
| `batcher.aura` | `(define (make-batcher batch-size) ...)`, `(define (batcher-size b) ...)`, `(define (batchify rows size) ...)`, `(define (rows->batches src size) ...)` |
| `scanner.aura` | `(define (make-scan source projection predicates batch-size) ...)`, `(define (scan-run scan) ...)`, `(define (scan-stats scan) ...)`, `(define (scan-rows-passed scan) ...)` |
| `stats.aura` | `(define (make-stats) ...)`, `(define (stats-tick! s rows-passed rows-scanned) ...)`, `(define (stats-rows-scanned s) ...)`, `(define (stats-rows-passed s) ...)`, `(define (stats-batches s) ...)`, `(define (stats-elapsed-us s start end) ...)` |
| `reporter.aura` | `(define (format-scan-report stats source projection pushdown-count batches-passed) ...)`, `(define (report-key-value k v) ...)`, `(define (print-report lines) ...)` |
| `main.aura` | driver: build source, projection, predicates, run scan, print report |

## Scenario steps (main.aura)

1. Define a small in-memory CSV as a list of rows with header `("id" "price" "qty" "region")`.
2. Build a datasource via `(make-rows-source header rows)`.
3. Build a projection requesting columns `("price" "qty")` via `(make-projection ...)`.
4. Build two predicates: `(make-predicate "price" ">=" 10)` and `(make-predicate "qty" "<" 100)`.
5. Extract pushdown predicates via `(extract-pushdown header preds)`.
6. Apply pushdown to source via `(apply-pushdown src p)`.
7. Create a batcher with size 3 via `(make-batcher 3)` and convert rows to batches via `(rows->batches ...)`.
8. Create a scan via `(make-scan ...)` and run it via `(scan-run scan)`.
9. For each projected column, call `(agg-count) (agg-sum) (agg-min) (agg-max) (agg-nulls)` on the scan's aggregator.
10. Gather stats via `(scan-stats scan)` and `(stats-elapsed-us ...)`.
11. Format the report via `(format-scan-report ...)` and print it via `(print-report lines)`.

## Anti-hardcode

- `main.aura` MUST call `make-rows-source`, `make-projection`, `make-predicate`, `extract-pushdown`, `apply-pushdown`, `make-batcher`, `rows->batches`, `make-scan`, and `scan-run` to compute every output line. No literal numeric values for `sum`, `min`, `max`, `count`, `nulls`, `rows_scanned`, or `rows_passed` may appear in `main.aura` — they must come from the aggregator/stats APIs.
- The pushed-down filter and the batch size must be parameters the modules consume; changing them changes the output.
- Reporter output must be assembled by iterating over the aggregator's column list, not by hardcoding column names in `main.aura`.

## How to run



All files load in order on a single Aura CLI invocation, sharing one top-level environment.
