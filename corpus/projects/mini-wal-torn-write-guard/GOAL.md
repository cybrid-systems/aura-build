# GOAL.md — mini-wal-torn-write-guard

## Overview

A toy mini-WAL (Write-Ahead Log) engine that demonstrates **torn-write detection and repair**. WAL frames are appended to an in-memory sector buffer that is chunked into 64-byte sectors; each sector carries a tail CRC32-style checksum (via a simple polynomial, not a real CRC) over its payload. The engine supports:

- Appending frames, splitting them across sector boundaries.
- A "crash" injection that deliberately truncates the last sector mid-frame (simulating a torn write).
- A `scan-and-repair` pass that walks sectors, validates tail checksums, and either truncates the partial sector or rebuilds it from prior committed frames.
- Restart recovery that re-opens the log and reports how many torn sectors were detected vs repaired.

All state lives in plain lists and alists; sectors are lists of bytes (small integers 0..255).

---

## Stdout contract

Exactly these KEY=value lines must be printed, in this order, one per line, no extra whitespace or blank lines:



Keys are fixed strings; values are computed by `main.aura` from real calls into the WAL API. `STATUS` is the literal string `OK` only if no errors occurred during recovery.

---

## Module table

| File | Required `(define (api …))` forms |
|------|------------------------------------|
| `bytes.aura` | `(define (api byte-xor a b))`, `(define (api byte=? a b))`, `(define (api checksum-sector payload))` |
| `sector.aura` | `(define (api make-sector size))`, `(define (api sector-add-byte! s b))`, `(define (api sector-full? s))`, `(define (api sector-payload s))`, `(define (api sector-checksum s))`, `(define (api sector-verify? s))`, `(define (api sector-clone s))` |
| `frame.aura` | `(define (api make-frame id payload))`, `(define (api frame-id f))`, `(define (api frame-payload f))`, `(define (api frame-bytes f))` |
| `wal.aura` | `(define (api wal-open size))`, `(define (api wal-append! w frame))`, `(define (api wal-sectors w))`, `(define (api wal-bytes w))`, `(define (api wal-verify w))`, `(define (api wal-repair! w))` |
| `crash.aura` | `(define (api crash-truncate-last-sector! w))`, `(define (api crash-clear-checksums! w))` |
| `repair.aura` | `(define (api repair-scan w))`, `(define (api repair-count-torn w))`, `(define (api repair-count-fixed w))` |
| `replay.aura` | `(define (api replay-frames w))`, `(define (api replay-count w))` |
| `recovery.aura` | `(define (api recovery-run w))` |
| `report.aura` | `(define (api report-build w))`, `(define (api report-get r key))` |
| `main.aura` | (no `api` define required; orchestrates and prints) |

`main.aura` is the last file loaded and the only one that calls `(display …)`.

---

## Scenario steps (main.aura)

1. `(set! w (wal-open 64))` — open a WAL with 64-byte sectors.
2. Append 8 frames (each 24 payload bytes) via `(wal-append! w (make-frame i payload))`, where `payload` is a 24-byte list derived from frame id (not literal `"frame-0"`, etc.).
3. Record pre-crash `wal-bytes` and `wal-verify` counts.
4. Inject a torn write: `(crash-truncate-last-sector! w)` then `(crash-clear-checksums! w)` on the truncated tail (touches 2 sectors).
5. Run `(repair-scan w)` and tally `TORN_SECTORS`, `REPAIRED`, `TRUNCATED` from the report.
6. Run `(recovery-run w)` to re-open and replay.
7. Read `REPLAYED` from `(replay-count w)` and `FINAL_BYTES` from `(wal-bytes w)`.
8. Print all keys via `(display …)` + `(newline)` in the order listed in the stdout contract.

`STATUS=OK` is printed only if `TORN_SECTORS = REPAIRED + TRUNCATED` and the recovered log passes `(wal-verify w)`.

---

## Anti-hardcode

- `main.aura` must call `wal-append!`, `crash-truncate-last-sector!`, `repair-scan`, `recovery-run`, `wal-bytes`, and `wal-verify` before printing any value.
- Frame payloads must be built per-frame (e.g. `(list i i i …)` 24 times) — not hardcoded byte literals matching the expected output.
- Checksum is computed by `(checksum-sector …)` from the byte module, not a constant.
- All numeric stdout values come from `(report-get r key)` or direct API calls, never from quoted literals like `"8"` or `"192"`.

---

## How to run



All files share one top-level environment; load order matters because `sector.aura` uses `(api byte-xor …)` defined in `bytes.aura`.

---
