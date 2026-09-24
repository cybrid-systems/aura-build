# Hash Join Probe Engine — GOAL.md

## Overview
A tiny in-memory query engine kernel that implements a **radix-partitioned grace hash join** between a build side (R) and a probe side (S), both keyed by a single integer join column. The engine exposes composable Aura APIs for hash table construction, partitioning, bloom-filter prefiltering, skewed-partition fallback, and probe-side result emission. The `main.aura` driver builds two small relations, runs the engine end-to-end, and prints a deterministic stdout contract summarizing the join result.

The implementation is purely educational: it uses **alist-backed** hash tables and **list-based** partitions. Radix partitioning, bloom filtering, and spill fallback are simulated with deterministic bookkeeping (counters and lists) rather than real I/O. All numbers in the contract are produced by walking the actual APIs — they are **not hardcoded literals**.

## Stdout contract
The scenario must print exactly these 14 KEY=value lines, in this order, one per line, terminated by a newline after the last value:



## Module table
Each `.aura` file defines the listed public `(define (api …))` forms. Files are loaded in order on a single Aura CLI invocation; later files may call earlier APIs. `main.aura` is loaded last and is the only file that performs top-level `display` calls.

| # | File | Required `(define (api …))` forms |
|---|---|---|
| 1 | `config.aura` | `(api-config-bits)`, `(api-config-partitions)` |
| 2 | `row.aura` | `(api-make-row k v)`, `(api-row-key r)`, `(api-row-value r)` |
| 3 | `relation.aura` | `(api-rel-build)`, `(api-rel-probe)`, `(api-rel-count rel)`, `(api-rel-rows rel)` |
| 4 | `bloom.aura` | `(api-bloom-empty size)`, `(api-bloom-add! bf k)`, `(api-bloom-maybe? bf k)` |
| 5 | `partition.aura` | `(api-partition-radix rows bits)`, `(api-partition-bucket parts k)` |
| 6 | `hashtable.aura` | `(api-ht-build rows)`, `(api-ht-probe ht k)`, `(api-ht-size ht)` |
| 7 | `spill.aura` | `(api-spill-record! pid rows)`, `(api-spill-count)`, `(api-spill-rows-for pid)` |
| 8 | `skew.aura` | `(api-skew-detect ht threshold)`, `(api-skew-fallback rows)` |
| 9 | `probe.aura` | `(api-probe-run ht probe-rows on-match on-miss)`, `(api-probe-stats)` |
| 10 | `result.aura` | `(api-result-build matched)`, `(api-result-tuples r)`, `(api-result-sum-k r)`, `(api-result-sum-v r)` |
| 11 | `metrics.aura` | `(api-metrics-bloom-positives)`, `(api-metrics-bloom-false-positives)` |
| 12 | `driver_data.aura` | `(api-driver-build-rows)`, `(api-driver-probe-rows)` |
| 13 | `pipeline.aura` | `(api-pipeline-execute)` |
| 14 | `main.aura` | (driver; no required `api` form, but performs `display` calls) |

## Scenario steps (`main.aura`)
1. Call `api-pipeline-execute` from `pipeline.aura` to drive the entire join; it returns an alist `(RESULT . result) (STATS . stats)`.
2. Print `BUILD_ROWS` = `(api-rel-count (api-rel-build))` and `PROBE_ROWS` = `(api-rel-count (api-rel-probe))` using the live relation APIs (not literals).
3. Print `PARTITIONS` and `BITS` from `(api-config-partitions)` / `(api-config-bits)`.
4. Print `BLOOM_POSITIVES` and `BLOOM_FALSE_POSITIVES` from `(api-metrics-bloom-positives)` / `(api-metrics-bloom-false-positives)`.
5. Print `SPILLED_PARTITIONS` and `SPILLED_ROWS` by walking the spill log via `(api-spill-count)` and the per-partition `(api-spill-rows-for pid)` summed for the spilled partition id.
6. Print `SKEW_FALLBACK_PARTITION` from `(api-skew-detect ht threshold)` (id of the skewed partition, or `0` if none; the reference data forces partition id `3`).
7. Print `MATCHED_ROWS` and `UNMATCHED_PROBE` = probe-rows − matched, by summing `api-probe-stats`.
8. Print `RESULT_TUPLES` = `(api-result-tuples result)`, `RESULT_SUM_K` = `(api-result-sum-k result)`, `RESULT_SUM_V` = `(api-result-sum-v result)`.
9. Every printed value must come from an API call above — no string literals like `"6"` or `"44"` may appear as `display` arguments.

## Anti-hardcode
- `main.aura` does **not** print any of the expected literals directly. Every value originates from `(api-…)` calls into the module chain. If you delete `pipeline.aura` or stub any module to return constants, the stdout contract will not match.
- The 4 matched row tuples are produced by `api-probe-run` walking the hash table built by `api-ht-build`; the sums come from `api-result-sum-k` / `api-result-sum-v` reducing those tuples.
- Bloom positives / false positives are real counters updated by `api-bloom-add!` and read by `api-probe-run`, not literals.
- Skew detection returns the partition id determined by `(api-skew-detect ht threshold)` comparing bucket sizes; it is not hardcoded to `3`.

## How to run

All 14 files share one top-level environment. `main.aura` is the entry point and is the only file that calls `display` / `newline`.
