# Fuzzy WAL Checkpoint Engine

## Overview
A miniature Write-Ahead Log (WAL) checkpoint engine that emits periodic *fuzzy* checkpoints. A fuzzy checkpoint records only the pages that were dirtied since the previous checkpoint, anchored to a starting Log Sequence Number (LSN). On restart the engine knows exactly where to begin replay, bounding the maximum recovery time. The system maintains an in-memory page table (dirtied bits), a redo log of records, and a checkpoint history. All state is held in lists/alists; no external dependencies.

## Exact stdout contract
Lines, in order (each `KEY=value`):



## Module table

| File | Required `(define (api …))` forms |
|------|------------------------------------|
| `constants.aura` | `(api min-page-id)`, `(api max-page-id)`, `(api lsn-start)`, `(api checkpoint-interval)`, `(api max-pages-per-fuzzy)` |
| `lsn.aura` | `(api make-lsn)`, `(api lsn? )`, `(api lsn=? )`, `(api lsn-advance)`, `(api lsn-diff)`, `(api lsn<=?)` |
| `page-table.aura` | `(api make-page-table)`, `(api page-dirty!)`, `(api page-dirty?)`, `(api dirty-pages)`, `(api dirty-page-count)`, `(api reset-dirty-bits!)`, `(api page-table-size)` |
| `redo-record.aura` | `(api make-redo)`, `(api redo? )`, `(api redo-page-id)`, `(api redo-lsn)`, `(api redo-size)` |
| `redo-log.aura` | `(api make-redo-log)`, `(api redo-log-append!)`, `(api redo-log-length)`, `(api redo-log-bytes)`, `(api redo-log-bytes-since!)` |
| `checkpoint.aura` | `(api make-checkpoint)`, `(api checkpoint? )`, `(api checkpoint-start-lsn)`, `(api checkpoint-end-lsn)`, `(api checkpoint-dirty-pages)` |
| `checkpoint-engine.aura` | `(api make-engine)`, `(api engine-emit-redo!)`, `(api engine-should-checkpoint?)`, `(api engine-emit-checkpoint!)`, `(api engine-stats)`, `(api engine-replay-from-lsn)`, `(api engine-max-replay-length)` |
| `fuzzy-collector.aura` | `(api make-fuzzy-collector)`, `(api fuzzy-collect!)`, `(api fuzzy-reset!)`, `(api fuzzy-count)` |
| `recovery.aura` | `(api recovery-replay-from)`, `(api recovery-scan-window)`, `(api recovery-reset-dirty-count)` |
| `stats.aura` | `(api make-stats)`, `(api stats-inc!)`, `(api stats-get)`, `(api stats-snapshot)` |
| `config.aura` | `(api default-config)`, `(api config-checkpoint-interval)`, `(api config-fuzzy-cap)` |
| `report.aura` | `(api report-stats)`, `(api report-snapshot)` |
| `main.aura` | (no exports — entry point; calls into modules above, then prints the 13 KEY=value lines) |

## Scenario steps (`main.aura`)

1. Load `constants.aura`, `config.aura`; build a default config and engine via `make-engine`.
2. Pretend to process a workload: loop `N=32` iterations. On each step, either dirt a random page (`page-dirty!`) and append a redo record (`engine-emit-redo!`), or — every `checkpoint-interval` records — ask `engine-should-checkpoint?`. When `#t`, call `engine-emit-checkpoint!` which internally uses `fuzzy-collect!` then `reset-dirty-bits!`.
3. After the loop, read `engine-stats` plus `redo-log-length` / `redo-log-bytes`.
4. Call `recovery-replay-from` to compute the recovery anchor and `recovery-scan-window` for max replay length.
5. Use `report-stats` to format each metric, then `(display …) (newline)` the 13 lines in the exact order above.

## Anti-hardcode
Every printed value must originate from API calls into the listed modules:
- `LSN`, `REDO_RECORDS`, `REDO_BYTES` come from `redo-log` queries.
- `PAGES_DIRTIED`, `DIRTY_BIT_RESET` come from `page-table` / `recovery`.
- `CHECKPOINT_COUNT`, `LAST_CHECKPOINT_LSN`, `CHECKPOINTS_EMITTED` come from `engine-stats`.
- `FUZZY_PAGES`, `REPLAY_FROM_LSN`, `MAX_REPLAY_LENGTH` come from `checkpoint-engine`/`recovery`/`fuzzy-collector`.
- `CHECKPOINT_INTERVAL` comes from `config`.

`main.aura` MUST NOT `(display "LSN=42")` style literal outputs — it must `(display (string-append "LSN=" (number->string …)))` where the number is the result of a real API call. The workload loop and random seed are deterministic but the *values* are computed.

## How to run

```sh
aura constants.aura config.aura lsn.aura page-table.aura redo-record.aura \
     redo-log.aura checkpoint.aura fuzzy-collector.aura stats.aura \
     recovery.aura checkpoint-engine.aura report.aura main.aura
json dogfood
{"files":["constants.aura","config.aura","lsn.aura","page-table.aura","redo-record.aura","redo-log.aura","checkpoint.aura","fuzzy-collector.aura","stats.aura","recovery.aura","checkpoint-engine.aura","report.aura","main.aura"],"entry":"main.aura","run_mode":"cli_multi","expect_keys":["LSN","PAGES_DIRTIED","CHECKPOINT_COUNT","LAST_CHECKPOINT_LSN","REDO_RECORDS","FUZZY_PAGES","REPLAY_FROM_LSN","MAX_REPLAY_LENGTH","CHECKPOINT_INTERVAL","DIRTY_BIT_RESET","REDO_BYTES","CHECKPOINTS_EMITTED"],"source_res":["\\(define\\s+\\(min-page-id\\b","\\(define\\s+\\(default-config\\b","\\(define\\s+\\(make-lsn\\b","\\(define\\s+\\(make-page-table\\b","\\(define\\s+\\(make-redo\\b","\\(define\\s+\\(make-redo-log\\b","\\(define\\s+\\(make-checkpoint\\b","\\(define\\s+\\(make-fuzzy-collector\\b","\\(define\\s+\\(make-stats\\b","\\(define\\s+\\(recovery-replay-from\\b","\\(define\\s+\\(make-engine\\b","\\(define\\s+\\(report-stats\\b"]}
```
