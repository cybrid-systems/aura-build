# GOAL.md — mini-wal-snapshot-retention

## Overview

A small, in-memory Write-Ahead Log (WAL) implementation in Aura that
supports appending records, taking snapshots at a given LSN, releasing
snapshots, and computing the **prune LSN** — the lowest LSN that is
still needed to satisfy any live snapshot. Segments whose high-water
LSN is strictly below the prune LSN may be safely reclaimed.

The "scenario" verifies the cooperative retention policy: appending
records at increasing LSNs, taking a snapshot, appending more records,
releasing the snapshot, and then asking the system which segments can
be pruned. All numbers in stdout are computed by the modules via the
documented APIs — not hardcoded.

## Exact stdout contract

The scenario must print exactly these 16 lines, in this order, each as
`KEY=value`:



Notes on semantics used by the verifier:

- `SEGk_HI` are the high-water LSNs of the first 5 segments after all
  50 appends are durably laid out (each segment holds 10 records, so
  highs are 9, 19, 29, 39, …).
- `PRUNE_LSN` is the LSN below which segments may be discarded. With
  no live snapshots it equals 0.
- `PRUNE_SEGMENTS` is the count of segments fully below `PRUNE_LSN`.
- `RECLAIM_BYTES` is the sum of `SEG_SIZE` over those segments (here 0
  because prune LSN is 0, so nothing is strictly below it).
- The `_REPLAY` keys confirm a snapshot taken at LSN 9 still reports
  the correct LSN after a "replay" pass over appended records.

## Module table

| File | Required `(define (api …))` forms |
|------|------------------------------------|
| `wal_segment.aura` | `(api seg-high seg)`, `(api seg-records seg)`, `(api seg-size seg)` |
| `wal_log.aura`     | `(api wal-append wal lsn payload)`, `(api wal-lsn wal)`, `(api wal-segments wal)`, `(api wal-record-count wal)` |
| `wal_snapshot.aura`| `(api snapshot-lsn snap)`, `(api snapshot-id snap)`, `(api snapshot-live? snap)`, `(api snapshot-release snap)` |
| `wal_manager.aura` | `(api manager-new)`, `(api manager-append mgr payload)`, `(api manager-lsn mgr)`, `(api manager-take-snapshot mgr lsn)`, `(api manager-snapshots mgr)`, `(api manager-prune-lsn mgr)`, `(api manager-prune-segments mgr)`, `(api manager-reclaim-bytes mgr)`, `(api manager-segments mgr)` |
| `wal_replay.aura`  | `(api replay-build mgr)`, `(api replay-snapshot-lsn replay)`, `(api replay-last-lsn replay)` |
| `wal_main.aura`    | `(main)` — the scenario driver; prints all KEY=… lines |

All files share one top-level via the Aura CLI multi-file loader. The
final loaded file (`wal_main.aura`) is the entry point.

## Scenario steps (wal_main.aura)

1. Create a manager: `(define mgr (manager-new))`.
2. Append 50 records, each carrying a tiny payload (e.g. the symbol
   index expressed as a string). The 50th append yields `LAST_LSN=49`
   because LSNs start at 0.
3. Read `wal-segments` of the underlying WAL and print `SEG0_HI …
   SEG4_HI`.
4. Take a snapshot at LSN 9, store it, print `SNAPSHOT_LSN` and
   `SNAPSHOT_COUNT`.
5. Release the snapshot, then print `AFTER_RELEASE_LIVE`.
6. Ask the manager for `manager-prune-lsn`, `manager-prune-segments`,
   `manager-reclaim-bytes`; print those.
7. Build a replay view via `replay-build` and print its snapshot LSN
   and last LSN (these confirm the manager can re-derive state from
   the WAL alone).

All keys above are produced only **after** the corresponding API calls
run.

## Anti-hardcode

`wal_main.aura` must not embed any of the expected numeric values as
literals except for trivial structural constants (`SEG_SIZE`, the count
of 50 appends, the LSN 9 at which the snapshot is taken). Every printed
`KEY=value` is the result of an API call into one of the modules:

- segment highs come from `seg-high` over `wal-segments`,
- `APPEND_COUNT` and `LAST_LSN` come from `wal-record-count` / `wal-lsn`,
- `SNAPSHOT_LSN` comes from `snapshot-lsn`,
- `AFTER_RELEASE_LIVE` comes from iterating `manager-snapshots` and
  checking `snapshot-live?`,
- `PRUNE_LSN` / `PRUNE_SEGMENTS` / `RECLAIM_BYTES` come from the
  manager's retention APIs,
- replay values come from `replay-build`.

The numbers 9, 19, 29, 39 are emergent from "50 appends × 10 per
segment" rather than typed in.

## How to run



The CLI loads each file in order into a shared top-level, then runs
`wal_main.aura` which calls `(main)` to produce the 16 `KEY=value`
lines on stdout.
