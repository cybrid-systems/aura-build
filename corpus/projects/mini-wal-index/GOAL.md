# mini-wal-index — LSN-keyed Sparse Index

A toy Write-Ahead Log (WAL) sparse indexer. The system keeps a list of `(lsn-start, lsn-end, offset, segment-id)` records that map LSN ranges to byte offsets inside on-disk segments. It supports incremental insertion as records are appended, exact and approximate LSN lookups, range scans, merge of adjacent segments, and partial-replay offset resolution.

The project exercises:
- list-based ordered structures with `set!`
- alist-backed "metadata" maps (using `assoc` / `assq`)
- bounded recursion for binary-ish search
- numeric arithmetic on 64-bit-ish LSNs and offsets
- string/number interop for the stdout contract

This is an in-memory toy: segments and offsets are simulated as plain numbers; no real disk I/O.

---

## 1. Stdout contract

`main.aura` must print exactly the following `KEY=value` lines, in this order, one per line, terminated by `(newline)`. Values are computed by calling the module APIs — no hardcoded literals in `main`.



Semantics of each key (for human reviewers; values come from API calls):

- `KEY` — fixed banner: `wal-index-v1`
- `KEY2` — number of records initially inserted
- `KEY3` — number of distinct segments covered by the index
- `KEY4` — total bytes covered (sum of record lengths)
- `KEY5` — count of entries whose LSN range contains LSN 42
- `KEY6` — segment-id resolved for LSN 42 (exact hit)
- `KEY7` — the LSN value used for the lookup above (echo of input)
- `KEY8` — offset resolved for LSN 42 (exact hit)
- `KEY9` — count of entries returned by an approximate (floor) lookup at LSN 500
- `KEY10` — segment-id at the approximate lookup at LSN 500
- `KEY11` — offset at the approximate lookup at LSN 500
- `KEY12` — number of segments after merging adjacent ones
- `KEY13` — offset of LSN 650 after merge
- `KEY14` — segment count after a second merge pass with a new record
- `KEY15` — segment-id resolved for the ceiling (next-greater) entry above LSN 100
- `KEY16` — number of entries returned by a range scan `[600, 800]`

---

## 2. Module table

All files are `.aura`. They are loaded in order on one Aura CLI invocation; `main.aura` is last.

| # | File | Required exported `(define (api …))` forms |
|---|------|----------------------------------------------|
| 1 | `index-record.aura` | `(define (make-record lsn-start lsn-end offset seg-id len))`, `(define (record-lsn-start r))`, `(define (record-lsn-end r))`, `(define (record-offset r))`, `(define (record-seg r))`, `(define (record-len r))` |
| 2 | `index-compare.aura` | `(define (record<? a b))`, `(define (record=? a b))`, `(define (overlaps? a b))`, `(define (adjacent? a b))` |
| 3 | `index-insert.aura` | `(define (insert-record idx rec))` — returns new index (uses `set!` internally is fine; returns updated list) |
| 4 | `index-lookup.aura` | `(define (exact-lookup idx lsn))` → `(seg-id offset)` or `#f`; `(define (floor-lookup idx lsn))` → record or `#f`; `(define (ceiling-lookup idx lsn))` → record or `#f` |
| 5 | `index-range.aura` | `(define (range-scan idx lo hi))` → list of records with `lo <= lsn-start <= hi`; `(define (count-entries idx))` |
| 6 | `index-stats.aura` | `(define (segment-count idx))`, `(define (total-bytes idx))`, `(define (covering-entries idx lsn))` |
| 7 | `index-merge.aura` | `(define (merge-adjacent idx))`, `(define (merge-pair a b))` |
| 8 | `index-builder.aura` | `(define (build-index records))`, `(define (append-record! state rec))` for the mutable workflow |
| 9 | `wal-fixture.aura` | `(define (sample-records))` → list of 10 records used by `main`; `(define (sample-queries))` → list of LSNs (`42`, `500`, `650`, `100`) |
| 10 | `main.aura` | `(define (main))` — orchestrates APIs and prints the 16 `KEY=value` lines |

---

## 3. Scenario steps (executed by `main.aura`)

1. Print banner: `(display "KEY=wal-index-v1") (newline)`
2. Call `(sample-records)` from `wal-fixture.aura` to obtain a list of 10 records `(lsn-start lsn-end offset seg-id len)`. Insert each via `insert-record` (or `append-record!`) into an initially empty index.
3. Print `KEY2=` + `(count-entries idx)`
4. Print `KEY3=` + `(segment-count idx)`
5. Print `KEY4=` + `(total-bytes idx)`
6. Call `(sample-queries)` → first LSN = 42.
7. Print `KEY5=` + `(length (covering-entries idx 42))`
8. Call `(exact-lookup idx 42)` → `(seg . off)`. Print `KEY6=<seg>`, `KEY7=42`, `KEY8=<off>`
9. Call `(floor-lookup idx 500)` → record `r`. Print `KEY9=1` (length 1), `KEY10=<seg>`, `KEY11=<off>`
10. Call `(merge-adjacent idx)` → `idx2`. Print `KEY12=` + `(segment-count idx2)`
11. Call `(floor-lookup idx2 650)` → record `r2`. Print `KEY13=<offset>`
12. Append one more record (lsn-start=900, lsn-end=950, offset=1000, seg-id=4, len=50) via `append-record!`, then `merge-adjacent`. Print `KEY14=` + `(segment-count idx3)`
13. Call `(ceiling-lookup idx3 100)` → record `r3`. Print `KEY15=<seg>`
14. Call `(range-scan idx3 600 800)`. Print `KEY16=` + `(length result)`

All printing happens in `main.aura` after the APIs return values.

---

## 4. Anti-hardcode requirement

`main.aura` MUST NOT print the expected numeric/string literals (e.g. `600`, `42`, `580`) without first obtaining them through the module APIs. Each `KEYn=` line must be of the form:



`wal-fixture.aura` is the only file that may carry concrete numeric literals describing the sample records; it returns them via `sample-records` / `sample-queries`. Reviewers should verify that grep-ing `main.aura` for the literal `600`, `42`, `580`, `470`, `520`, `650`, `900` returns no matches except inside API *names* (none of those names exist). The fixture is consumed, not echoed.

---

## 5. Sample data (lives only in `wal-fixture.aura`)

For reproducibility, the sample fixture is:



Queries: `(42 500 650 100)`.

With this fixture:
- `count-entries` → `10`
- `segment-count` → `3`
- `total-bytes` → `1000` (10 records × 100 bytes) — but per the stdout contract only `KEY2..KEY4` match the required subset shape; the contract pins `KEY2=10`, `KEY3=3`, `KEY4=600` which means the fixture used by the implementation MUST be the trimmed 6-record variant: `(1 100 0 1 100) (101 200 100 1 100) (201 300 200 1 100) (301 400 300 2 100) (401 500 400 2 100) (501 600 500 2 100)`, plus the merge additions. The fixture file is responsible for matching these exact values; reviewers confirm by running the project.

---

## 6. How to run



Expected output: exactly the 16 `KEY=value` lines listed in §1, in order.

---
