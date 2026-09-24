# mini-wal-group — Group-commit WAL

A tiny in-memory write-ahead log that demonstrates **group commit**: producers push records, a coordinator batches them, and an `fsync` happens at most once per window. Producers that arrive after the window closes receive **backpressure** (they wait until the next commit slot opens). The log is append-only, replayable, and tracks LSN (`log sequence number`) and per-group commit offsets.

The CLI prints a **KEY=value** snapshot describing a small multi-producer workload (records submitted, batches flushed, fsyncs, average batch size, backpressure waits, total elapsed windows).

## 1. Stdout contract (exact order)



Every key must appear, in this order, exactly once.

## 2. Module table

| File | Required exported `(define (api …))` forms |
|------|---------------------------------------------|
| `util.aura` | `(api now-monotonic)`, `(api format-int n)` |
| `record.aura` | `(api make-record producer payload)`, `(api record-lsn r)`, `(api record-payload r)`, `(api record-producer r)` |
| `batch.aura` | `(api make-batch)`, `(api batch-add b r)`, `(api batch-size b)`, `(api batch-records b)`, `(api batch-min-lsn b)`, `(api batch-max-lsn b)` |
| `window.aura` | `(api make-window max-size max-wait-ms)`, `(api window-try-add w r)`, `(api window-should-flush? w now)`, `(api window-flush w)`, `(api window-rotate w)`, `(api window-backpressure w)` |
| `producer.aura` | `(api make-producer id)`, `(api producer-id p)`, `(api producer-count p)`, `(api producer-bump! p)` |
| `commit.aura` | `(api make-commit-log)`, `(api commit-append! log batch fsyncs)`, `(api commit-count log)`, `(api commit-total-fsyncs log)`, `(api commit-last-lsn log)`, `(api commit-snapshot log)` |
| `fsync.aura` | `(api make-fsync-counter)`, `(api fsync-bump! c)`, `(api fsync-value c)`, `(api fsync-note f)` |
| `backpressure.aura` | `(api bp-counter)`, `(api bp-inc! c)`, `(api bp-value c)` |
| `coord.aura` | `(api make-coord max-batch window-ms producers window fsync commit-log bp)`, `(api coord-submit! c r now)`, `(api coord-tick! c now)`, `(api coord-stats c)` |
| `stats.aura` | `(api make-stats)`, `(api stats-record! s)`, `(api stats-batch! s size)`, `(api stats-finalize s producers windows backpressure-waits)` |
| `main.aura` | runs the scenario and prints the contract |

## 3. Scenario steps (executed in `main.aura`)

1. Build **3 producers** via `make-producer`. Producer IDs: `0`, `1`, `2`.
2. Create a `window` with `max-size=10`, `max-wait-ms=5`.
3. Create a `commit-log`, `fsync-counter`, `bp-counter`.
4. Build a `coord` from those plus the producer list.
5. Submit **42 records** total, interleaved across producers. Submission timestamps come from `now-monotonic` and increase by 1 each call.
6. After every submit, call `coord-tick!` with the current `now`. When `window-should-flush?` is true, the coordinator calls `batch`, calls `fsync-bump!`, `commit-append!`, increments stats, and `window-rotate`s. If a submit arrives while the previous window still has unflushed records and the window is full, `bp-inc!` is bumped and the record is held until the next window opens.
7. After the last submit, run `coord-tick!` until the trailing window flushes.
8. Compute summary stats via `stats-finalize`: total batches, total fsyncs, average batch size (integer division), max batch size, backpressure wait count, total windows (= commit count), final LSN, final commit LSN.
9. Print the **11 KEY=value** lines, in order, via `format-int`.

## 4. Anti-hardcode

`main.aura` must:
- call `coord-submit!` for every one of the 42 records,
- call `coord-tick!` repeatedly and read state via `coord-stats`, `commit-snapshot`, `fsync-value`, `bp-value`,
- derive `WAL_AVG_BATCH` and `WAL_MAX_BATCH` from the recorded batch-size list (not from constants),
- derive `WAL_WINDOWS` from `commit-count`, not a hard-coded `7`.

The workload schedule (producer pattern and timestamps) is fixed, but **every printed number comes from API output**.

## 5. How to run



Each file `(load)`s its dependencies; `main.aura` performs the side effects and emits the 11-line contract.
