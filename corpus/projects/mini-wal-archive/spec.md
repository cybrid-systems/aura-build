# Tiered WAL Archiver — GOAL.md

## Overview
A toy in-memory tiered Write-Ahead Log (WAL) archiver written in Aura. It simulates
moving aged WAL segments from a **hot** tier (fast local disk) to a **cold** tier
(object storage) once they exceed a configurable age/byte threshold, enforces a
retention policy (drop the oldest cold segments beyond the cap), and reports
stats about each tier. Everything lives in plain lists / alists — no real I/O.

The CLI is invoked with multiple `.aura` files on a single command line, sharing
a top-level environment. `main.aura` is the entry point and prints the final
stdout contract.

---

## Stdout Contract (exact order)



13 keys. `main.aura` must `display` each line via `(display "KEY=val") (newline)`.

---

## Module Table

| File | Required exported `(define (api …))` |
|------|--------------------------------------|
| `wal-types.aura` | `make-segment`, `segment-id`, `segment-bytes`, `segment-age-ms`, `segment-tier` |
| `wal-store.aura` | `make-store`, `store-add!`, `store-all`, `store-tier`, `store-size`, `store-bytes`, `store-oldest-age` |
| `wal-ingest.aura` | `ingest-segment!` |
| `wal-clock.aura` | `current-ms`, `advance-ms!` |
| `wal-age.aura` | `age-sweep!`, `aged-segment?` |
| `wal-archive.aura` | `archive-sweep!`, `tier-move!` |
| `wal-retention.aura` | `enforce-retention!`, `retention-policy` |
| `wal-stats.aura` | `compute-stats`, `format-stats` |
| `wal-log.aura` | `log-event!`, `drain-log` |
| `wal-config.aura` | `default-config`, `config-archive-age-ms`, `config-archive-bytes`, `config-retain-max` |
| `wal-run.aura` | `run-archive-pipeline!` |
| `main.aura` | (entry; orchestrates and prints contract) |

All modules except `main.aura` only **define** the listed APIs. `main.aura` is
the only file that calls `(display …)` for the stdout contract.

---

## Scenario Steps (executed by `main.aura`)

1. Load defaults via `(default-config)` to get `age=5000 ms`, `bytes=10000`,
   `retain=5`. Bind as `cfg`.
2. Create two stores via `(make-store 'hot)` and `(make-store 'cold)`.
3. Initialize the log via `(log-event! 'ingest)` priming.
4. Ingest 10 segments of `id=1..10`, each `10000` bytes, spaced 1000 ms apart
   using `(advance-ms! 1000)` between ingests. All land in `hot`.
   - Total: 10 hot segs / 100000 bytes; clock ends at `10000`.
5. Call `(age-sweep! hot cfg)` → marks segs with `age >= 5000` as archive-candidates.
   Append `'age-sweep` to the log.
6. Call `(archive-sweep! hot cold cfg)` → moves all 10 aged segments into `cold`,
   counting moved=10 / bytes=100000. Append `'archive-sweep`.
7. Re-ingest 3 fresh segments (`id=11..13`) at clock=11000, 12000, 13000 into
   `hot` (30000 bytes, oldest age 12000 ms). Append `'ingest` per ingest.
8. Call `(enforce-retention! cold cfg)` → cold has 10 segs, retain=5, so drop
   the oldest 5 (by id ascending). Dropped count = 5, retained cold = 5
   (`id=6..10`), cold bytes = 50000. Append `'retention`.
   - **Target values use a smaller fixture**: to hit the printed contract,
     `main.aura` should instead ingest 10 segs, archive 7 (only those aged past
     threshold at first sweep), then add 3 more hot, then enforce retention
     dropping the 2 oldest cold beyond retain=5. See `run-archive-pipeline!`
     which encapsulates this exact sequence.
9. Call `(run-archive-pipeline! …)` (defined in `wal-run.aura`) which performs
   steps 4–8 with the precise numbers needed.
10. Compute stats: `(compute-stats hot cold)` → returns an alist with the 11
    numeric keys listed in the contract.
11. Format run log via `(drain-log)` → joined by `|` to yield `WAL_ARCHIVE_RUN_LOG`.
12. Print each `KEY=value` line in the exact order shown in the contract.

The printed numbers are produced by walking the stores (`store-size`,
`store-bytes`, `store-oldest-age`) and accumulator counters returned by the
archiver/retention APIs — they are **not** literal constants.

---

## Anti-Hardcode

`main.aura` must:
- Call `(run-archive-pipeline! …)` (or the equivalent chain of `ingest-segment!`,
  `age-sweep!`, `archive-sweep!`, `enforce-retention!`) before printing.
- Pull every printed value from store accessors, stats alist, or
  `(drain-log)` output.
- It is **not** allowed to write e.g. `(display "WAL_ARCHIVE_HOT_SEGMENTS=3")`
  with a hardcoded `3`; the `3` must come from `(store-size hot)`.

A reference grader will re-run the pipeline with a perturbed fixture
(different segment counts / sizes) and confirm the keys still track reality.

---

## How to Run



All files share one top-level; `main.aura` is the entry point and produces the
stdout contract above.

---
