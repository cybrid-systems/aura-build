```markdown
# MVCC Transactions over WAL — `mini-wal-txn`

## Overview

A toy multi-version concurrency control (MVCC) layer sitting on top of an
append-only write-ahead log (WAL). Keys are strings mapped to the latest
visible value for a transaction. Every write produces a new versioned record
(`key@txn=value`); reads use snapshot isolation against a chosen txn id.
The WAL supports begin/commit/abort, transactional get/put, snapshot reads,
and conflict detection for two concurrent writers updating the same key.

All state lives in-memory; the WAL is a list of records. This is a teaching
toy, not a production database. About 14 small Aura files.

## Exact stdout contract

The program prints 12 KEY=value lines, in this order:



## Module table

| File | Required `define` forms |
|------|-------------------------|
| `constants.aura` | `(define (api wal-tag))`, `(define (api txn-tag))`, `(define (api committed-tag))`, `(define (api aborted-tag))`, `(define (api current-txn-id))` (returns 0 at load time) |
| `wal.aura` | `(define (api make-wal))` → `'()`, `(define (api wal-append wal rec))`, `(define (api wal-length wal))`, `(define (api wal-records wal))`, `(define (api wal-last wal))` |
| `version.aura` | `(define (api make-version key value txn-id op))` → `'(key . (value txn-id op))` list, `(define (api version-key v))`, `(define (api version-value v))`, `(define (api version-txn v))`, `(define (api version-op v))` |
| `txn.aura` | `(define (api make-txn id))` → `'(id state versions)` list, `(define (api txn-id t))`, `(define (api txn-state t))` (set! via `txn-set-state!`), `(define (api txn-versions t))`, `(define (api txn-add-version! t v))` |
| `mvcc-store.aura` | `(define (api make-store))` → list of `(key . latest-version)` alist + committed list, `(define (api store-put! store key value txn-id))`, `(define (api store-commit! store txn wal))`, `(define (api store-snapshot-get store key snapshot-txn))`, `(define (api store-conflict? store key txn-id))`, `(define (api store-active-count store))` |
| `snapshot.aura` | `(define (api make-snapshot txn-id))`, `(define (api snapshot-id s))`, `(define (api snapshot-visible? snap version))` (visible if version-txn <= snapshot-id and committed) |
| `conflict.aura` | `(define (api detect-conflict store key writer-txn))` → `#t/#f` based on whether an uncommitted or newer-committed writer touched the key |
| `txn-mgr.aura` | `(define (api mgr-begin))`, `(define (api mgr-commit txn store wal))`, `(define (api mgr-abort txn store))`, `(define (api mgr-active-txns store))` |
| `counters.aura` | `(define (api counter-new))` → 0, `(define (api counter-inc! c))`, `(define (api counter-value c))`, `(define (api counter-add! c n))` |
| `alists.aura` | `(define (api alist-set alist key val))`, `(define (api alist-get alist key))`, `(define (api alist-keys alist))`, `(define (api alist-count alist))` |
| `records.aura` | `(define (api record-txn rec))`, `(define (api record-key rec))`, `(define (api record-value rec))`, `(define (api record-op rec))` (a record is `'(op key value txn-id)`) |
| `trace.aura` | `(define (api trace-new))`, `(define (api trace-add! tr k v))`, `(define (api trace-get tr k))`, `(define (api trace-emit tr))` prints every k=v line via display/newline in order added |
| `scenario.aura` | `(define (api run-scenario))` — builds store/wal/txn-mgr/trace, runs 4 transactions (2 commit, 2 abort), takes 3 snapshots, runs the steps below, returns trace |
| `main.aura` | `(define (api main))` — calls `(run-scenario)`, then `(display "TXN_COUNT=") (display (trace-get tr 'txn-count)) …` for every required key, in contract order |

## Scenario steps

`run-scenario` performs exactly these actions (via the module APIs above,
not by hardcoded numbers):

1. `(set! current-txn-id 0)`
2. Build `(wal (make-wal))`, `(store (make-store))`, `(tr (trace-new))`.
3. Begin **tx1** (id=1): put `x=v1`, put `y=v1`, commit.
4. Begin **tx2** (id=2): put `x=v2`. Take **snapshot A** at txn id=2 (reads `x`).
   tx2 aborts.
5. Begin **tx3** (id=3): put `y=v2`, commit.
6. Begin **tx4** (id=4): put `x=v2`, put `y=v3`, commit.
7. Take **snapshot B** at txn id=3 reading `x`.
8. Take **snapshot C** at txn id=4 reading `x`.
9. Attempt tx5 (id=5) write to `x` while tx4 is uncommitted → record
   `CONFLICT_DETECTED=#t`, abort tx5.
10. Attempt tx6 (id=6) write to `y` after tx3 committed but with no overlap
    on the working set → conflict? returns `#f`, commit tx6 only if no
    conflict; we instead mark it aborted to keep counts balanced.
11. Tally: total transactions begun = 4 (tx1..tx4); aborted = 2 (tx2, tx5);
    committed = 2 (tx1, tx3 then tx4 → counted as 2 active commits);
    actually committed = 2 (tx1, tx4) — tx3 also commits, so 3 commits.
    Use `mgr-active-txns` after all calls to derive `ACTIVE_AT_END=0`.
    Use `store-active-count` for cross-check.
12. Snapshot reads: at A (id=2) `x` → `v1`; at B (id=3) `x` → `v1`;
    at C (id=4) `x` → `v2`. Final `x` after tx4 commit = `v2`;
    final `y` after tx3 + tx4 = `v3`.
13. `KEYS_WRITTEN = (alist-count (alist-keys written-alist))` = 2 (`x`,`y`),
    but each commit appends a version record per key, so total put-version
    records emitted = 6 (tx1: 2, tx3: 1, tx4: 2, tx2: 1).
    `WAL_RECORDS = (wal-length wal)` = 6 put-records + 3 commit records = 9.
14. Trace emits the 12 required keys.

## Anti-hardcode

`main.aura` must:
- Call `(run-scenario)` to obtain a live trace built by `mvcc-store`,
  `txn-mgr`, `wal`, and `snapshot` operations.
- Look up every KEY with `(trace-get tr 'KEY)` and `display` it — no
  string literals for the values.
- The values derive from `(wal-length wal)`, `(alist-count …)`,
  `(store-snapshot-get …)`, `(mgr-active-txns store)`, etc.

If `run-scenario` is replaced with a stub that just `display`s the literal
contract values, the program fails the "API-not-called" check.

## How to run



The single Aura CLI invocation loads all files into one top-level,
executes `(main)`, and prints the 12 KEY=value lines in order.
