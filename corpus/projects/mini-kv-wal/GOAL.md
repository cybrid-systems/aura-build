```markdown
# mini-kv-wal — KV Store Backed by a Segmented WAL

## Overview
A small in-memory key/value store whose durable state is reconstructed from a
segmented write-ahead log (WAL). Every mutation (`put`, `del`) is first
appended to the active WAL segment as a length-prefixed record; when a segment
fills, it is sealed and a fresh segment is opened. On startup, segments are
replayed in order to rebuild the memtable. The project demonstrates the
classic LSM-style durability trick (commit-then-ack, replay-on-reopen) using
only the toy Aura primitives: lists, alists, `with-output-to-file` /
`with-input-from-file`, and a tiny fixed-length framing scheme (`#u8` headers
written as text lines are forbidden — we serialize each record as a single
UTF-8 line: `<key>\t<flag>\t<value>` where `flag` is `0` for put and `1` for
del; `key` and `value` are themselves required to contain no tab/newline).

The store supports:

* `put!` / `del!` — append a record, then mutate the memtable.
* `get` — memtable lookup returning the live value, the tombstone sentinel
  `'deleted`, or `'missing`.
* `scan` — range scan over the memtable (alphabetical, list-of-pairs).
* `fsync` — flush the current segment.
* `recover` — replay all segments in numeric order to rebuild the memtable.

There is no background compactor; sealed segments are simply kept on disk.

## Stdout contract

The scenario (`main.aura`) must print exactly these KEY=value lines, in this
order, one per line. No other output is allowed.



That is 15 keys.

## Module table

| File | Required exported `define` forms |
| --- | --- |
| `encoding.aura` | `(encode-record key flag value)`, `(decode-record line)`, `(record-flag-put)`, `(record-flag-del)` |
| `segment.aura` | `(make-segment dir idx)`, `(segment-path seg)`, `(segment-write-line seg line)`, `(segment-flush seg)`, `(segment-sealed? seg)`, `(segment-seal! seg)`, `(segment-line-count seg)` |
| `wal.aura` | `(wal-open dir)`, `(wal-active seg)`, `(wal-append! wal key flag value)`, `(wal-seal-active! wal)`, `(wal-segments wal)`, `(wal-replay wal)`, `(wal-fsync wal)` |
| `memtable.aura` | `(make-memtable)`, `(memtable-put! m key value)`, `(memtable-del! m key)`, `(memtable-get m key)`, `(memtable-scan m)`, `(memtable-count m)` |
| `kvstore.aura` | `(kv-open dir)`, `(kv-put! kv key value)`, `(kv-del! kv key)`, `(kv-get kv key)`, `(kv-scan kv)`, `(kv-recover! kv)`, `(kv-fsync kv)` |
| `metrics.aura` | `(make-counters)`, `(counters-inc! c name)`, `(counters-add! c name n)`, `(counters-value c name)`, `(counters-snapshot c)` |
| `paths.aura` | `(ensure-dir! dir)`, `(list-segment-files dir)`, `(next-segment-index files)`, `(join-path dir name)` |
| `strings1.aura` | `(string-contains? s sub)`, `(string-split-tab s)`, `(safe-key? k)`, `(format-kv key value)` |
| `tombstone.aura` | `(deleted-sentinel)`, `(deleted? v)`, `(missing-sentinel)`, `(missing? v)` |
| `compare.aura` | `(string<? a b)`, `(sort-pairs pairs)` |
| `scenario.aura` | `(run-scenario kv)` — orchestrates the steps below and returns an alist `((KEY . "value") …)` of results. Returns exactly the 15 expected keys with string values. |
| `main.aura` | `(main)` — the entry point. Loads the modules in order, opens a fresh temporary store directory, calls `run-scenario`, prints the 15 KEY=value lines in order, then prints `FINAL_FSYNC=ok` after an explicit `kv-fsync`. |

## Scenario steps (executed by `scenario.aura`)

`run-scenario` performs the following, building an alist of results, then
hands that alist to `main.aura` which prints the lines.

1. **Reset** — wipe / create the store dir (`ensure-dir!` on a temp path).
2. **Open** — call `kv-open` (which internally `wal-open`s, creates segment 0,
   and `kv-recover!`s). Record `SEGMENTS_OPENED` = 1 initially.
3. **Puts** — write the following 5 keys in alphabetical order, calling
   `kv-put!` and incrementing `PUT_COUNT` each time:
   * `alpha = apple`
   * `bravo = banana`
   * `charlie = cherry`
   * `delta = date`
   * `foxtrot = fig`
4. **Seal** — call `kv-fsync` followed by `wal-seal-active!` so the next write
   starts a new segment. Record `SEGMENTS_OPENED` = 2.
5. **Delete** — call `kv-del!` on `delta` and `tango`, incrementing
   `DEL_COUNT`.
6. **Seal again** — `wal-seal-active!`. Record `SEGMENTS_OPENED` = 3.
7. **Puts** — write `echo = egg` (a 7th mutation, but `PUT_COUNT` only counts
   the original 5; we count it in `metrics` but the printed key remains
   `PUT_COUNT=5`). *(Internal note: `scenario.aura` tracks the total put
   count separately but the reported key is the spec'd value.)*
8. **Reads** — using `kv-get`:
   * `alpha` → `"apple"` → `GET_HIT_ALPHA`
   * `bravo` → `"banana"` → `GET_HIT_BRAVO`
   * `charlie` → `"cherry"` → `GET_HIT_CHARLIE`
   * `tango` → `deleted-sentinel` → render as `<deleted>` → `GET_DELETED_TANGO`
   * `zulu` → `missing-sentinel` → render as `<missing>` → `GET_MISSING_ZULU`
9. **Scan** — call `kv-scan`, count the live keys
   (`alpha, bravo, charlie, foxtrot, echo` → 5 live), but only the first 3
   alphabetically (`alpha, bravo, charlie`) are reported in `SCAN_COUNT=3`
   (the spec defines `SCAN_COUNT` as the number of entries returned by a
   scan with an in-scenario prefix filter applied in `scenario.aura`).
10. **Recover** — close the store conceptually by calling `kv-recover!`
    after reopening: simulate a restart by calling `kv-open` again on the
    same dir (which internally does `wal-replay` over all 3 sealed
    segments). After replay, `memtable-count` must equal 5 live keys
    (`alpha, bravo, charlie, foxtrot, echo`; `delta` and `tango` are
    tombstones).
11. **Verify recovery** — `kv-get alpha → apple`, `kv-get charlie → cherry`,
    `kv-get foxtrot → fig`. Record `RECOVERED_KEYS=3` (the number of
    verification reads performed).
12. **Final fsync** — `kv-fsync`. Record `FINAL_FSYNC=ok`.

All counter increments go through `metrics.aura` so the main file is forced
to call into the module API rather than hardcoding the numbers.

## Anti-hardcode

`main.aura` is not allowed to short-circuit the scenario:

* It may not `display` any of the 15 expected literal strings unless they
  were obtained from a return value of a module API.
* The 5 `PUT_COUNT`, 2 `DEL_COUNT`, and 3 `SEGMENTS_OPENED` values must come
  from `counters-value` reads on a counters object that was actually
  incremented inside `run-scenario` via `kv-put!` / `kv-del!` /
  `wal-seal-active!`.
* `GET_*` values must come from `kv-get` return values; `SCAN_COUNT` from
  `kv-scan`; `RECOVERED_*` from `kv-get` after a fresh `kv-open`; and
  `FINAL_FSYNC` is set by calling `kv-fsync` and matching its `'ok`
  return.

A reviewer can swap out `scenario.aura` for one that uses different keys
or values and the 15-line stdout contract will simply change accordingly;
nothing in `main.aura` hardcodes those strings.

## How to run



The Aura CLI loads each file in order into a shared top-level environment,
then executes the `(main)` defined in `main.aura`, which prints the 15
KEY=value lines and exits.

## Expected behavior

After execution the store directory (a temp path chosen by `paths.aura`)
contains three sealed segment files:



Each line inside a segment is of the form `<key>\t<flag>\t<value>` (put) or
`<key>\t<flag>\t` (del), and replaying them in numeric order reproduces the
final memtable: `alpha=apple`, `bravo=banana`, `charlie=cherry`,
`echo=egg`, `foxtrot=fig`, with `delta` and `tango` recorded as deletions.
json dogfood
{
  "files": [
    "encoding.aura",
    "segment.aura",
    "wal.aura",
    "memtable.aura",
    "kvstore.aura",
    "metrics.aura",
    "paths.aura",
    "strings1.aura",
    "tombstone.aura",
    "compare.aura",
    "scenario.aura",
    "main.aura"
  ],
  "entry": "main.aura",
  "run_mode": "cli_multi",
  "expect_keys": [
    "SCENARIO",
    "SEGMENTS_OPENED",
    "PUT_COUNT",
    "DEL_COUNT",
    "GET_HIT_ALPHA",
    "GET_HIT_BRAVO",
    "GET_HIT_CHARLIE",
    "GET_DELETED_TANGO",
    "GET_MISSING_ZULU",
    "SCAN_COUNT",
    "RECOVERED_KEYS",
    "RECOVERED_ALPHA",
    "RECOVERED_CHARLIE",
    "RECOVERED_FOXTROT",
    "FINAL_FSYNC"
  ],
  "source_res": [
    "\\(define\\s+\\(encode-record\\b",
    "\\(define\\s+\\(decode-record\\b",
    "\\(define\\s+\\(record-flag-put\\b",
    "\\(define\\s+\\(record-flag-del\\b",
    "\\(define\\s+\\(make-segment\\b",
    "\\(define\\s+\\(segment-path\\b",
    "\\(define\\s+\\(segment-write-line\\b",
    "\\(define\\s+\\(segment-flush\\b",
    "\\(define\\s+\\(segment-sealed\\?\\b",
    "\\(define\\s+\\(segment-seal!\\b",
    "\\(define\\s+\\(segment-line-count\\b",
    "\\(define\\s+\\(wal-open\\b",
    "\\(define\\s+\\(wal-active\\b",
    "\\(define\\s+\\(wal-append!\\b",
    "\\(define\\s+\\(wal-seal-active!\\b",
    "\\(define\\s+\\(wal-segments\\b",
    "\\(define\\s+\\(wal-replay\\b",
    "\\(define\\s+\\(wal-fsync\\b",
    "\\(define\\s+\\(make-memtable\\b",
    "\\(define\\s+\\(memtable-put!\\b",
    "\\(define\\s+\\(memtable-del!\\b",
    "\\(define\\s+\\(memtable-get\\b",
    "\\(define\\s+\\(memtable-scan\\b",
    "\\(define\\s+\\(memtable-count\\b",
    "\\(define\\s+\\(kv-open\\b",
    "\\(define\\s+\\(kv-put!\\b",
    "\\(define\\s+\\(kv-del!\\b",
    "\\(define\\s+\\(kv-get\\b",
    "\\(define\\s+\\(kv-scan\\b",
    "\\(define\\s+\\(kv-recover!\\b",
    "\\(define\\s+\\(kv-fsync\\b",
    "\\(define\\s+\\(make-counters\\b",
    "\\(define\\s+\\(counters-inc!\\b",
    "\\(define\\s+\\(counters-add!\\b",
    "\\(define\\s+\\(counters-value\\b",
    "\\(define\\s+\\(counters-snapshot\\b",
    "\\(define\\s+\\(ensure-dir!\\b",
    "\\(define\\s+\\(list-segment-files\\b",
    "\\(define\\s+\\(next-segment-index\\b",
    "\\(define\\s+\\(join-path\\b",
    "\\(define\\s+\\(string-contains\\?\\b",
    "\\(define\\s+\\(string-split-tab\\b",
    "\\(define\\s+\\(safe-key\\?\\b",
    "\\(define\\s+\\(format-kv\\b",
    "\\(define\\s+\\(deleted-sentinel\\b",
    "\\(define\\s+\\(deleted\\?\\b",
    "\\(define\\s+\\(missing-sentinel\\b",
    "\\(define\\s+\\(missing\\?\\b",
    "\\(define\\s+\\(string<?\\b",
    "\\(define\\s+\\(sort-pairs\\b",
    "\\(define\\s+\\(run-scenario\\b",
    "\\(define\\s+\\(main\\b"
  ]
}
```
