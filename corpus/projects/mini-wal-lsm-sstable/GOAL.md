# LSM Tree with WAL and SSTable Compaction

## Overview

A toy in-memory **Log-Structured Merge (LSM) tree** storage engine in Aura. The engine maintains an in-memory **memtable** (a sorted list of key/value entries), appends every mutation to an **append-only Write-Ahead Log (WAL)** so uncommitted data survives crashes, and periodically **flushes** the memtable into an **immutable SSTable** file. Reads walk the memtable first, then SSTables from newest to oldest. A **manifest** records which SSTables are live so the engine can **replay** on startup and recover the last consistent state. **Leveled compaction** merges SSTables at one level into the next when a level exceeds a size threshold, removing overwritten/deleted keys and rewriting the manifest atomically. All files are simulated in-memory as Aura strings — there is no real disk I/O — but the algorithms (flush, replay, compaction, crash safety) are real.

## Stdout Contract

The program must print exactly these KEY=value lines, in this order:



## Module Table

| File | Required API Forms |
|------|--------------------|
| `wal.aura` | `(define (wal-open path))`, `(define (wal-append wal key value))`, `(define (wal-replay wal))`, `(define (wal-size wal))`, `(define (wal-clear wal))` |
| `memtable.aura` | `(define (memtable-new))`, `(define (memtable-put mt k v))`, `(define (memtable-delete mt k))`, `(define (memtable-get mt k))`, `(define (memtable-size mt))`, `(define (memtable-snapshot mt))`, `(define (memtable-clear mt))` |
| `sstable.aura` | `(define (sstable-flush entries level path))`, `(define (sstable-entries sst))`, `(define (sstable-min-key sst))`, `(define (sstable-max-key sst))`, `(define (sstable-level sst))`, `(define (sstable-path sst))`, `(define (sstable-count-keys sst))` |
| `manifest.aura` | `(define (manifest-new))`, `(define (manifest-add mfst sst))`, `(define (manifest-remove mfst path))`, `(define (manifest-at-level mfst lvl))`, `(define (manifest-snapshot mfst))`, `(define (manifest-restore snap))`, `(define (manifest-count mfst))` |
| `compaction.aura` | `(define (compaction-needed? mfst level threshold))`, `(define (compaction-select mfst level))`, `(define (compaction-merge ssts new-level new-path))`, `(define (compaction-run engine level))` |
| `read_path.aura` | `(define (read-memtable mt k))`, `(define (read-sstables mfst k))`, `(define (engine-get engine k))` |
| `crash_recovery.aura` | `(define (crash-snapshot engine))`, `(define (crash-recover snap wal mfst))` |
| `engine.aura` | `(define (engine-open path))`, `(define (engine-put engine k v))`, `(define (engine-delete engine k))`, `(define (engine-get engine k))`, `(define (engine-flush engine))`, `(define (engine-compact engine level))`, `(define (engine-stats engine))` |
| `keycodec.aura` | `(define (key-compare a b))`, `(define (key-decode s))`, `(define (key-encode n))` |
| `valuecodec.aura` | `(define (value-encode v))`, `(define (value-decode s))`, `(define (tombstone? v))`, `(define (tombstone-sentinel))` |
| `counters.aura` | `(define (counters-new))`, `(define (counters-inc c name))`, `(define (counters-get c name))`, `(define (counters-snapshot c))` |
| `sorted_merge.aura` | `(define (sorted-merge lists))`, `(define (sorted-dedup-last lists))`, `(define (sorted-range ssts ssts lo hi))` |
| `sstable_io.aura` | `(define (sstable-io-write entries path))`, `(define (sstable-io-read path))`, `(define (sstable-io-exists? path))` |
| `level_picker.aura` | `(define (level-picker-select mfst level))`, `(define (level-picker-threshold level))`, `(define (level-picker-next-level level))` |
| `main.aura` | (entry point — calls APIs from all other modules and prints KEY=value lines) |

## Scenario Steps (main.aura)

1. Print `ENGINE_STARTED=true` after `engine-open` returns.
2. Issue 20 `engine-put` calls with keys `KEY_0000000000` … `KEY_0000000019`. Print `WAL_APPENDS=20` from the counters returned by the WAL module.
3. Print `MEMTABLE_SIZE=20` from `memtable-size`.
4. Call `engine-flush` once. Print `SSTABLE_COUNT=1` from `manifest-count`.
5. Call `engine-get "KEY_0000000050"` (note: not yet inserted). Print `GET_KEY=KEY_0000000050` and `GET_MISS=1`.
6. Insert `KEY_0000000050` with value `"VAL_050"`. Overwrite 4 prior keys (e.g. `KEY_0000000000..0003`) and delete 3 keys (`KEY_0000000010..0012`). Print `PUT_OVERWRITES=5` and `DELETES=3` from counters.
7. `engine-get "KEY_0000000050"` should hit memtable. Print `GET_HIT_SSTABLE=0`.
8. Flush again. Now SSTable count becomes 2. Print `LEVEL0_FLUSHED=2` (cumulative flushes) and `LEVEL0_FILES=2` (files currently at L0).
9. `engine-get "KEY_0000000010"` must return the tombstone. Print `TOMBSTONE_HITS=1` and `GET_HIT_SSTABLE=1`.
10. Force `engine-compact` at level 0. Print `COMPACTION_INPUT=2`, `COMPACTION_OUTPUT=1`, `LEVEL0_FILES=0`, `LEVEL1_FILES=1`.
11. Print `TOTAL_KEYS=12` from a sum of `sstable-count-keys` over L1 files (20 inserted − 5 overwrites netted against 3 deletes ⇒ 12 unique surviving keys).
12. Simulate crash: call `crash-snapshot` and a fresh `engine-open` on a path that has no manifest yet. Replay WAL by walking append log via `wal-replay`, restoring manifest via `manifest-restore`. Print `WAL_REPLAYED=20`.

## Anti-Hardcode

main.aura must NOT print the expected values without calling the engine APIs. Every printed value must come from a counter, from `memtable-size`, from `manifest-count`, from `sstable-count-keys`, from `engine-get`, from `engine-compact`, or from `wal-replay`. No string literal `"20"`, `"1"`, `"12"` may appear on the right-hand side of any KEY=value line. Use `(number->string (counter-get …))` or equivalent computation. The 20 keys must be generated by `(key-encode n)` for `n` in 0..19 — not hardcoded list literals of all 20 keys.

## How to Run



The Aura runtime loads all files into a shared top-level, then main.aura executes the scenario and prints the 16 KEY=value lines.
