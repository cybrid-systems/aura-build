```markdown
# mini-wal-direct-io

A miniature, in-memory simulation of a **Direct-IO Write-Ahead Log** with an
aligned appender. The runtime is Aura (Lisp-like); we model an `O_DIRECT`-style
writer that bypasses the page cache, enforces 4 KiB sector alignment, packs
records through a simple bump allocator, and tracks write barriers per
transaction. Although no real syscalls are issued (the "disk" is a list-backed
byte buffer), every API in this project mirrors what a kernel-level WAL
implementation would expose to user space.

The project demonstrates:
- aligned direct append of fixed-size records,
- record layout computed from a free-list allocator,
- per-transaction barrier (commit/flush) accounting,
- crash-safe tail truncation,
- deterministic recovery replay from the simulated WAL.

## Stdout contract

The scenario must print exactly these `KEY=value` lines, in this order, with a
single trailing newline. Values are computed from the module APIs at runtime;
they must not be hard-coded constants in `main.aura`.



## Module table

All files share one top-level Aura process; `main.aura` is loaded last and only
prints after invoking the APIs.

| File | Required exported `define` forms |
|------|----------------------------------|
| `wal_types.aura` | `(define (wal-make-config ...))`, `(define (wal-sector-size cfg))`, `(define (wal-direct? cfg))`, `(define (wal-version cfg))` |
| `wal_alloc.aura` | `(define (allocator-new slots))`, `(define (allocator-take alloc))`, `(define (allocator-free alloc))`, `(define (allocator-reset alloc))` |
| `wal_record.aura` | `(define (record-make txid kind payload))`, `(define (record-len rec))`, `(define (record-txid rec))`, `(define (record-crc rec))` |
| `wal_crc.aura` | `(define (crc32 bytes))`, `(define (crc=? a b))` |
| `wal_align.aura` | `(define (align-up n base))`, `(define (align-check n base))`, `(define (direct-append buf record sector-size))` |
| `wal_buffer.aura` | `(define (buffer-new size))`, `(define (buffer-tail buf))`, `(define (buffer-slice buf start end))`, `(define (buffer-truncate buf offset))` |
| `wal_barrier.aura` | `(define (barrier-new))`, `(define (barrier-issue br bytes))`, `(define (barrier-count br))`, `(define (barrier-bytes br))` |
| `wal_writer.aura` | `(define (writer-open cfg))`, `(define (writer-append! w rec))`, `(define (writer-barrier! w br))`, `(define (writer-tail w))`, `(define (writer-direct? w))` |
| `wal_replay.aura` | `(define (replay-open buf sector-size))`, `(define (replay-next rep))`, `(define (replay-count rep))`, `(define (replay-tail rep))` |
| `wal_crash.aura` | `(define (crash-inject-bad-crc buf offset))` |
| `wal_report.aura` | `(define (report-build writer alloc barrier replay))` |
| `main.aura` | (entrypoint; calls APIs and prints keys) |

## Scenario steps performed in `main.aura`

1. Build a WAL config with `wal-make-config`, capture `wal-version`,
   `wal-sector-size`, `wal-direct?`.
2. Open a direct writer with `writer-open`.
3. Create a bump allocator of 64 slots via `allocator-new`; record free count.
4. Loop 20 times: take a slot with `allocator-take`, build a record with
   `record-make` (txid cycles 1..5, payload size derived from slot index so that
   `record-len` varies), append with `writer-append!` (which internally performs
   `align-up` against `sector-size` and invokes `direct-append`).
5. Every 4 appends, issue a barrier with `barrier-issue` and call
   `writer-barrier!` so barriered-byte accounting matches `record-len` totals.
6. Capture writer tail with `writer-tail` (expected `TAIL_OFFSET`).
7. Corrupt one byte mid-log via `crash-inject-bad-crc`, then open a replayer
   with `replay-open`. Count mismatches by comparing `crc32` of each
   `buffer-slice` against `record-crc`; tally zeros for `CRC_MISMATCHES`.
8. Drain the replayer with `replay-next` until empty; record replayed count
   and final tail offset.
9. Truncate nothing — recovery tail equals writer tail — print all keys
   exactly once via `display`.

## Anti-hardcode notes

- `main.aura` may not embed the expected numeric answers as literals; every
  value printed must come from an API call (e.g. `(number->string (writer-tail w))`,
  `(if (wal-direct? cfg) "#t" "#f")`).
- Record payload sizes are derived from `(allocator-take alloc)` results, not
  from a hard-coded list.
- The 20-record loop, the 4-step barrier cadence, and the 5-txid cycle are all
  expressed by recursion/`modulo` over runtime values, not by literal sequences.
- `CRC_MISMATCHES` must be counted by iterating the buffer slice list; a
  literal `0` is not permitted.

## How to run



The Aura runtime loads each file in order on a single invocation; `main.aura`
prints the 12 `KEY=value` lines defined above.
