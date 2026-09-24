# Mini WAL Fsync-Batch — Project Goal

## Overview

Build an in-memory, multi-file Aura simulation of a **Write-Ahead Log (WAL) with group-commit fsync batching**. The system models concurrent writers appending transaction records to a staging buffer; a group commit coordinator periodically drains the buffer, fsyncs once per batch, and acknowledges writers whose records landed in the same sync. Each writer also observes `commit-wait` semantics: a writer may request synchronous commit and block (busy-poll on a per-txn flag) until the coordinator has persisted its LSN.

The project is *toy/educational*: no real `fsync(2)` is performed; the WAL file content and the per-batch fsync counter are stored in plain Aura data structures. The point is to demonstrate the **protocol**, not durability across crashes.

All file/module names below are descriptive and **final**.

---

## Exact stdout contract (KEY=value lines, in this order)

1. `BATCHES_FLUSHED=3`
2. `FSYNC_CALLS=3`
3. `RECORDS_PERSISTED=12`
4. `WRITERS=4`
5. `MAX_BATCH_SIZE=4`
6. `GROUP_COMMIT_WAITERS=1`
7. `LSN_FIRST=1`
8. `LSN_LAST=12`
9. `W0_LSN=3`
10. `W1_LSN=5`
11. `W2_LSN=8`
12. `W3_LSN=12`
13. `SYNC_COMMIT_OK=#t`
14. `ASYNC_COMMIT_OK=#t`
15. `WAL_BYTES=96`
16. `DURABILITY=#f`

(The reference scenario described in §Scenario must cause exactly these lines to be printed, in exactly this order. Values are measured by the harness from the implementation; the goal only fixes the keys and their order.)

---

## Module table (filename → required exported `define`s)

| File | Required exports |
|---|---|
| `wal_config.aura` | `(api wal-default-config)`, `(api wal-max-batch-size cfg)`, `(api wal-fsync-on-commit? cfg)` |
| `wal_lsn.aura` | `(api lsn-next cur)`, `(api lsn-equal? a b)`, `(api lsn->string l)` |
| `wal_record.aura` | `(api make-record tx-id payload)`, `(api record-tx-id r)`, `(api record-payload r)`, `(api record->bytes r)` |
| `wal_buffer.aura` | `(api buffer-new cfg)`, `(api buffer-append! buf rec)`, `(api buffer-drain! buf)`, `(api buffer-size buf)`, `(api buffer-empty? buf)` |
| `wal_writer.aura` | `(api writer-new id buf lsn-start)`, `(api writer-append! w payload)`, `(api writer-flush-sync! w coordinator)`, `(api writer-flush-async! w coordinator)`, `(api writer-current-lsn w)`, `(api writer-committed-lsn w)` |
| `wal_coordinator.aura` | `(api coordinator-new cfg wal)`, `(api coordinator-group-commit! c)`, `(api coordinator-fsync-count c)`, `(api coordinator-batches-flushed c)`, `(api coordinator-wal c)` |
| `wal_segment.aura` | `(api segment-new)`, `(api segment-append! seg bytes)`, `(api segment-byte-count seg)`, `(api segment-fsync! seg)`, `(api segment-snapshot seg)` |
| `wal_waiter.aura` | `(api waiter-new lsn)`, `(api waiter-signal! w lsn-broadcast)`, `(api waiter-ready? w)`, `(api waiter-poll w)` |
| `wal_metrics.aura` | `(api metrics-new)`, `(api metrics-record-batch! m n)`, `(api metrics-record-fsync! m)`, `(api metrics-batches m)`, `(api metrics-fsyncs m)`, `(api metrics-records m)` |
| `wal_runtime.aura` | `(api runtime-new cfg)`, `(api runtime-register-writer! rt w)`, `(api runtime-tick! rt)`, `(api runtime-writers rt)`, `(api runtime-should-fsync? rt)`, `(api runtime-fsync-target rt)` |
| `main.aura` | (scenario driver; no `api` form required — calls everything above) |

The runtime/CLI loads files in the order listed; top-level state (writers, coordinator, segment, metrics, runtime) is built in `main.aura`.

---

## Scenario steps (executed in `main.aura`)

The driver must perform these steps in order; **the KEY=… lines are printed only after the corresponding step has actually invoked module APIs**. Strings alone are never printed without computation behind them.

1. **Build config** via `wal-default-config` (returns an alist with `max-batch-size`, `fsync-on-commit`, …).
2. **Create the WAL segment** with `segment-new`; remember its handle.
3. **Create the coordinator** with `coordinator-new` against the config and segment.
4. **Create the runtime** with `runtime-new` and register 4 writers (`W0..W3`) via `runtime-register-writer!`. Each writer starts at LSN = previous-last + 1.
5. **Writers append records** (3 records per writer × 4 writers = 12 records total) using `writer-append!`. The buffer accepts them through `buffer-append!`.
6. **W3 requests synchronous commit** by calling `writer-flush-sync!`; this enqueues a `waiter-new` that will be polled.
7. **W0..W2 request async commit** via `writer-flush-async!` (no waiter created).
8. **Runtime tick** via `runtime-tick!`: the coordinator drains the buffer in groups of ≤ `wal-max-batch-size cfg` (= 4), appending each record's bytes to the segment, then performing a single `segment-fsync!` per drained group. After each group, broadcast the highest LSN to the waiter if present.
9. The sync waiter is busy-polled with `waiter-poll` until `waiter-ready?` returns `#t`.
10. **Collect metrics**: batches flushed, fsync calls, records persisted; read `writer-current-lsn` / `writer-committed-lsn` for each writer; read `coordinator-fsync-count`, `coordinator-batches-flushed`, `coordinator-wal`, `segment-byte-count`, `segment-snapshot`.
11. **Print** the 16 KEY=… lines, in the exact order listed in §stdout contract. (`SYNC_COMMIT_OK` reflects the waiter's eventual ready? state; `DURABILITY` is hard-coded `#f` because this is an in-memory toy WAL.)
12. **Exit cleanly** (no extra output).

**Anti-hardcode rule.** `main.aura` may not simply `display` the expected strings. Every printed value must come from querying a module API after the runtime has actually ticked. For example:

- `BATCHES_FLUSHED` comes from `coordinator-batches-flushed`.
- `W0_LSN` … `W3_LSN` come from `writer-current-lsn` on each writer.
- `WAL_BYTES` comes from `segment-byte-count`.
- `WAL_BYTES` is `(* 12 8) = 96` only because `record->bytes` deterministically produces 8 bytes per record; the driver does **not** compute the multiplication itself — it reads the segment's byte count.

---

## How to run

```bash
aura wal_config.aura wal_lsn.aura wal_record.aura wal_buffer.aura \
      wal_writer.aura wal_coordinator.aura wal_segment.aura \
      wal_waiter.aura wal_metrics.aura wal_runtime.aura main.aura
json dogfood
{
  "files": [
    "wal_config.aura",
    "wal_lsn.aura",
    "wal_record.aura",
    "wal_buffer.aura",
    "wal_writer.aura",
    "wal_coordinator.aura",
    "wal_segment.aura",
    "wal_waiter.aura",
    "wal_metrics.aura",
    "wal_runtime.aura",
    "main.aura"
  ],
  "entry": "main.aura",
  "run_mode": "cli_multi",
  "expect_keys": [
    "BATCHES_FLUSHED",
    "FSYNC_CALLS",
    "RECORDS_PERSISTED",
    "WRITERS",
    "MAX_BATCH_SIZE",
    "GROUP_COMMIT_WAITERS",
    "LSN_FIRST",
    "LSN_LAST",
    "W0_LSN",
    "W1_LSN",
    "W2_LSN",
    "W3_LSN",
    "SYNC_COMMIT_OK",
    "ASYNC_COMMIT_OK",
    "WAL_BYTES",
    "DURABILITY"
  ],
  "source_res": [
    "\\(define\\s+\\(wal-default-config\\b",
    "\\(define\\s+\\(wal-max-batch-size\\b",
    "\\(define\\s+\\(wal-fsync-on-commit\\?\\b",
    "\\(define\\s+\\(lsn-next\\b",
    "\\(define\\s+\\(lsn-equal\\?\\b",
    "\\(define\\s+\\(lsn->string\\b",
    "\\(define\\s+\\(make-record\\b",
    "\\(define\\s+\\(record-tx-id\\b",
    "\\(define\\s+\\(record-payload\\b",
    "\\(define\\s+\\(record->bytes\\b",
    "\\(define\\s+\\(buffer-new\\b",
    "\\(define\\s+\\(buffer-append!\\b",
    "\\(define\\s+\\(buffer-drain!\\b",
    "\\(define\\s+\\(buffer-size\\b",
    "\\(define\\s+\\(buffer-empty\\?\\b",
    "\\(define\\s+\\(writer-new\\b",
    "\\(define\\s+\\(writer-append!\\b",
    "\\(define\\s+\\(writer-flush-sync!\\b",
    "\\(define\\s+\\(writer-flush-async!\\b",
    "\\(define\\s+\\(writer-current-lsn\\b",
    "\\(define\\s+\\(writer-committed-lsn\\b",
    "\\(define\\s+\\(coordinator-new\\b",
    "\\(define\\s+\\(coordinator-group-commit!\\b",
    "\\(define\\s+\\(coordinator-fsync-count\\b",
    "\\(define\\s+\\(coordinator-batches-flushed\\b",
    "\\(define\\s+\\(coordinator-wal\\b",
    "\\(define\\s+\\(segment-new\\b",
    "\\(define\\s+\\(segment-append!\\b",
    "\\(define\\s+\\(segment-byte-count\\b",
    "\\(define\\s+\\(segment-fsync!\\b",
    "\\(define\\s+\\(segment-snapshot\\b",
    "\\(define\\s+\\(waiter-new\\b",
    "\\(define\\s+\\(waiter-signal!\\b",
    "\\(define\\s+\\(waiter-ready\\?\\b",
    "\\(define\\s+\\(waiter-poll\\b",
    "\\(define\\s+\\(metrics-new\\b",
    "\\(define\\s+\\(metrics-record-batch!\\b",
    "\\(define\\s+\\(metrics-record-fsync!\\b",
    "\\(define\\s+\\(metrics-batches\\b",
    "\\(define\\s+\\(metrics-fsyncs\\b",
    "\\(define\\s+\\(metrics-records\\b",
    "\\(define\\s+\\(runtime-new\\b",
    "\\(define\\s+\\(runtime-register-writer!\\b",
    "\\(define\\s+\\(runtime-tick!\\b",
    "\\(define\\s+\\(runtime-writers\\b",
    "\\(define\\s+\\(runtime-should-fsync\\?\\b",
    "\\(define\\s+\\(runtime-fsync-target\\b"
  ]
}
```
