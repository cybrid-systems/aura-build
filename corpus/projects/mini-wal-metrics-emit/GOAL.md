# mini-wal-metrics-emit — WAL observability and metrics emitter

A toy in-process metrics layer for a write-ahead log. Tracks monotonic counters
(bytes appended, records appended, fsync calls), gauges (backlog bytes,
dirty pages), a simple latency histogram (fsync microseconds), and replay
progress (records replayed vs. expected). Emits periodic snapshots to stdout
in a stable `KEY=value` format so external scrapers can ingest them.

The goal is a small, dependency-free, single-pass Aura implementation that
exposes a clean API for the rest of a hypothetical WAL subsystem to call, and
emits a final metrics summary on shutdown.

## 1. Stdout contract (exact order)

The program prints **exactly these 13 lines**, in this order, prefixed by
`[metrics] `. Trailing whitespace is forbidden. Numbers are printed via
`number->string` (no padding, no thousands separators).



Percentile values are integer microseconds. `replay_complete` is `0` or `1`.

## 2. Module table

| File | Required exported `(define (api …) …)` forms |
|---|---|
| `metrics-types.aura` | `(define (api make-counter) ...)`, `(define (api counter-inc!) ...)`, `(define (api counter-add!) ...)`, `(define (api counter-value) ...)`, `(define (api make-gauge) ...)`, `(define (api gauge-set!) ...)`, `(define (api gauge-value) ...)` |
| `metrics-histogram.aura` | `(define (api make-histogram) ...)`, `(define (api histogram-observe!) ...)`, `(define (api histogram-quantile) ...)`, `(define (api histogram-count) ...)` |
| `metrics-registry.aura` | `(define (api registry-create) ...)`, `(define (api registry-register!) ...)`, `(define (api registry-get) ...)`, `(define (api registry-snapshot) ...)` |
| `wal-counters.aura` | `(define (api wal-default-registry) ...)`, `(define (api wal-inc-records!) ...)`, `(define (api wal-inc-bytes!) ...)`, `(define (api wal-inc-fsync!) ...)`, `(define (api wal-inc-fsync-errors!) ...)`, `(define (api wal-set-backlog!) ...)`, `(define (api wal-set-dirty!) ...)` |
| `wal-fsync.aura` | `(define (api fsync-record!) ...)`, `(define (api fsync-latency-us) ...)` |
| `wal-backlog.aura` | `(define (api backlog-push!) ...)`, `(define (api backlog-drain!) ...)`, `(define (api backlog-size-bytes) ...)` |
| `wal-replay.aura` | `(define (api replay-begin!) ...)`, `(define (api replay-step!) ...)`, `(define (api replay-progress) ...)` |
| `metrics-emit.aura` | `(define (api emit-snapshot!) ...)`, `(define (api format-line) ...)` |
| `main.aura` | (drives the scenario; calls every API above) |

All `define`s listed under “required exported” must actually appear at
top-level in the corresponding file. Names use the `(api …)` wrapper as a
tag for the grader; the inner identifier is what main.aura references.

## 3. Scenario steps (in `main.aura`)

1. Load order is the table order above; `main.aura` runs last.
2. Obtain the default WAL registry via `wal-default-registry` and verify it
   is non-null using the registry API.
3. Simulate 10 appends of 64 bytes each through `wal-inc-records!` /
   `wal-inc-bytes!`, and adjust the gauge for backlog/dirty between calls
   so the final gauges are non-zero.
4. Call `fsync-record!` five times. Each call records one fsync counter,
   one histogram observation (latencies in microseconds chosen to make
   p50/p95/p99 distinguishable integers), and increments fsync-errors on
   the 3rd call only.
5. Push 5 items onto the backlog via `backlog-push!` (each 32 bytes), then
   drain 3 via `backlog-drain!`. Final `backlog-size-bytes` must be 64.
6. Begin a replay of expected = 7 records via `replay-begin!`. Step
   through 7 calls to `replay-step!`. Read `replay-progress` and assert
   the returned pair `(records . expected)` equals `(7 . 7)` and the
   complete flag is `#t`.
7. Build a local registry, register a counter and a histogram, then call
   `registry-snapshot` and verify it returns an alist with both keys
   present and matching values.
8. Compute uptime in milliseconds from a captured start tick.
9. Call `emit-snapshot!` with the WAL registry to print all 13 lines in
   the contract order. main.aura must not `display` the literal metric
   strings; it must call `format-line` for each KEY and let
   `emit-snapshot!` order them.

## 4. Anti-hardcode

- `main.aura` does **not** call `(display "[metrics] wal.records_appended_total=10")`
  or any other literal expected line. Every value reaching stdout is
  fetched through the registry / histogram / replay APIs and formatted
  by `format-line`.
- Percentiles are computed by `histogram-quantile`, not hardcoded.
- The scenario is observable: removing any step changes at least one
  printed value.

## 5. How to run



All files share one top-level environment; later files see earlier
`define`s. `main.aura` is the entry point and is the only file that
performs `display` / `newline`.
