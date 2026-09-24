# WAL Segment Manager — Project GOAL

## Overview

A miniature Write-Ahead Log (WAL) segment manager written in Aura. The system manages
paged log segments backed by an in-memory file abstraction. Each page carries a checksum
that is verified on read; recovery scans segments from the tail, truncating any torn
(tail-corrupted) records so the log resumes at a clean boundary. The manager supports
append, fsync, segment rotation, CRC32-style checksum verification, and a `RECOVER`
operation that returns the highest consistent LSN.

The project exercises: ring buffers over a paged file, a checksum primitive,
torn-write detection by re-checksumming tail pages, and segment rotation logic.
All persistence is in-memory (a `vector`-like list of bytes), so no real disk I/O
occurs — but the API surface matches what a real WAL manager would expose.

## Stdout Contract (exact order)

The program must print exactly these 16 `KEY=value` lines, in this order:



## Module Table

| File | Required API forms |
|---|---|
| `crc32.aura` | `(define (api-crc32 bytes))`, `(define (api-crc-update crc acc))` |
| `page.aura` | `(define (api-make-page lsn payload))`, `(define (api-page-lsn p))`, `(define (api-page-bytes p))`, `(define (api-page-verify? p))` |
| `segment.aura` | `(define (api-make-segment id path page-size))`, `(define (api-segment-id s))`, `(define (api-segment-write! s page))`, `(define (api-segment-pages s))`, `(define (api-segment-bytes s))`, `(define (api-segment-fsync! s))`, `(define (api-segment-tail-ok? s))` |
| `wal.aura` | `(define (api-wal-open dir page-size))`, `(define (api-wal-append! wal payload))`, `(define (api-wal-fsync! wal))`, `(define (api-wal-lsn wal))`, `(define (api-wal-recover wal))`, `(define (api-wal-rotate! wal))`, `(define (api-wal-active-seg wal))`, `(define (api-wal-segments wal))`, `(define (api-wal-replay wal))` |
| `wal_replay.aura` | `(define (api-replay-segment seg))` returning `(lsn . bytes-restored)` |
| `torn_write.aura` | `(define (api-detect-torn seg))`, `(define (api-truncate-torn! seg))` |
| `recovery.aura` | `(define (api-recover-wal wal))` returning `(recovered-lsn truncated-bytes)` |
| `lsn.aura` | `(define (api-next-lsn wal))`, `(define (api-reset-lsn! wal))` |
| `stats.aura` | `(define (api-wal-stats wal))` returning a stats struct |
| `main.aura` | entry point: opens WAL, appends 42 frames, rotates, simulates recovery, prints stdout contract |

## Scenario Steps (main.aura)

1. `(api-wal-open "wal-dir" 128)` — open WAL with 128-byte page size.
2. Loop 42 times: append a 96-byte payload (`api-wal-append!`), advancing LSN to 42.
3. Capture `api-wal-fsync!` result and segment page count before rotation.
4. `api-wal-rotate!` — force a new empty segment.
5. `api-wal-recover` — must return LSN=42, truncated=0 (clean tail).
6. `api-replay-segment` on segment 0 to count frames restored.
7. Compute checksum validity of segment 0 via `api-segment-tail-ok?`.
8. Collect `api-wal-stats` and format all 16 keys, then `display` each `KEY=value` line.

## Anti-Hardcode

`main.aura` MUST call the module APIs above. If `RECOVER_LSN`, `TOTAL_RECS`,
`SEG1_BYTES`, or `TRUNCATED_BYTES` are written as literal strings without
invoking `api-wal-recover`, `api-wal-stats`, `api-wal-segments`, or
`api-truncate-torn!`, the project fails the anti-hardcode check. At least
one dynamic decision (e.g. segment rotation triggered by byte threshold,
or torn-write truncation result) must visibly depend on API return values.

## How to Run
