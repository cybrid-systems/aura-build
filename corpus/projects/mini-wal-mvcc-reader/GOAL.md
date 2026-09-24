# Mini WAL MVCC Reader — GOAL.md

## Overview

A toy, in-memory **MVCC (Multi-Version Concurrency Control) reader** backed by a **single append-only Write-Ahead Log (WAL)**. WAL records are written once and never mutated; each record carries a `txn-id` and a `prev-version` pointer forming a **version chain** per key. Readers take a **snapshot id** and traverse the chain to find the latest committed version visible to that snapshot — yielding snapshot-isolated reads without a separate version store.

The system is split into 13 Aura modules: low-level WAL append/read, key/value record encoding, per-key version chain maintenance, transaction commit bookkeeping, snapshot creation, visibility checks, MVCC read resolution, and a main harness that exercises it all.

## Stdout Contract (exact lines, in order)



(15 keys; values are computed from API calls — not hardcoded.)

## Module Table

| File | Required `(define (api …))` forms |
|------|------------------------------------|
| `wal-record.aura` | `(api wal-record-make txn-id op key value prev-version)`, `(api wal-record-op rec)`, `(api wal-record-key rec)`, `(api wal-record-value rec)`, `(api wal-record-txn rec)`, `(api wal-record-prev rec)` |
| `wal-bytes.aura` | `(api wal-bytes-encode rec)`, `(api wal-bytes-decode bytes)` |
| `wal-store.aura` | `(api wal-store-init)`, `(api wal-store-append store bytes)`, `(api wal-store-len store)`, `(api wal-store-ref store idx)`, `(api wal-store-bytes store)` |
| `wal.aura` | `(api wal-append-record! store rec)`, `(api wal-read-record store idx)`, `(api wal-total-bytes store)` |
| `txn-table.aura` | `(api txn-table-init)`, `(api txn-table-begin! table txn-id)`, `(api txn-table-commit! table txn-id)`, `(api txn-table-abort! table txn-id)`, `(api txn-table-status table txn-id)`, `(api txn-table-active-count table)`, `(api txn-table-committed-count table)` |
| `snapshot-table.aura` | `(api snapshot-table-init)`, `(api snapshot-table-take! table snap-id at-txn-id)`, `(api snapshot-table-snap-txn table snap-id)`, `(api snapshot-table-count table)` |
| `chain-index.aura` | `(api chain-index-init)`, `(api chain-index-set! idx key head-idx)`, `(api chain-index-get idx key)`, `(api chain-index-keys idx)`, `(api chain-index-count idx)`, `(api chain-index-max-length idx)` |
| `version-resolve.aura` | `(api version-resolve walk-state snap-txn-id is-committed? record-at)`, `(api version-resolve-visible? snap-txn-id is-committed? rec)` |
| `mvcc-reader.aura` | `(api mvcc-reader-init wal chain-idx txn-tab)`, `(api mvcc-reader-get reader snap-id key)`, `(api mvcc-reader-stats reader)`, `(api mvcc-reader-update! reader txn-id key value)`, `(api mvcc-reader-finalize reader)` |
| `scenario-writes.aura` | `(api scenario-build-writes wal chain idx txn-tab)` |
| `scenario-reads.aura` | `(api scenario-build-reads reader snap-tab)` |
| `scenario-stats.aura` | `(api scenario-collect reader wal txn-tab snap-tab chain-idx)` |
| `main.aura` | `(api main-run)` |

## Scenario Steps (executed in `main.aura`)

1. Initialize WAL store, chain index, txn table, snapshot table, MVCC reader.
2. Begin several txns; append WAL records forming per-key version chains (some txns later commit, some abort).
3. Take a few snapshots at different `at-txn-id` watermarks.
4. Issue snapshot-isolated reads via `(mvcc-reader-get …)` for keys across snapshots; tally visible / not-visible / aborted / miss outcomes.
5. Finalize reader (scan chain index to materialize current KV pairs).
6. Print the 15 `KEY=…` lines in order, computed from API return values (e.g. `(wal-store-length store)`, `(txn-table-active-count table)`, `(chain-index-max-length idx)`, `(mvcc-reader-stats reader)`, etc.).

## Anti-Hardcode

`main.aura` must:
- Call `wal-append-record!` / `mvcc-reader-update!` to actually build the chains.
- Call `txn-table-begin!`, `txn-table-commit!`, `txn-table-abort!` so counts are real.
- Call `snapshot-table-take!` so `(snapshot-table-count …)` is non-trivial.
- Call `mvcc-reader-get` so `read_visible_total` / `read_not_visible_total` / `read_aborted_total` / `read_snapshot_misses` come from the reader's accumulator, not literals.
- Call `mvcc-reader-finalize` so `final_kv_pairs` is computed from the chain index.
- Only `display` values returned by APIs — no bare string literals for counts.

## How to Run



Loads all 13 files in one shared top-level; `main.aura` prints the 15 `KEY=…` lines.
