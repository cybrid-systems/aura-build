```markdown
# mini-btree-idx — B-Tree Secondary Index

A toy, in-memory B-tree secondary index implemented in Aura. Supports ordered
insertion of (key, primary-key, version-tuple) records, point lookup, range
scan, prefix scan, optional prefix-compressed keys, and MVCC-aware visibility
(version filtering). Persistent in the sense that the index lives across the
single CLI invocation; on reload the tree is rebuilt from an event log.

This is a teaching project — no on-disk fsync, no real pager, no real
concurrency. Every "API" below is an ordinary `define` in some `*.aura` file.

---

## 1. Exact stdout contract

After all `*.aura` files are loaded in order and `main.aura` finishes, the
process must print exactly the following 14 `KEY=value` lines on stdout, in this
order, each terminated by `\n`, with no other output between them:



Order matters. The grader compares stdout token-for-token against this list.
Any extra `display`/`newline` outside these 14 lines is a failure.

`KEYS_INSERTED`, `NODES_CREATED`, `TREE_HEIGHT`, `POINT_HIT`, `POINT_MISS`,
`RANGE_COUNT`, `PREFIX_COUNT`, `MVCC_VISIBLE`, `MVCC_HIDDEN`,
`COMPRESS_BYTES`, `RAW_BYTES` are non-negative integers.
`RANGE_FIRST`, `RANGE_LAST`, `PREFIX_FIRST` are string keys present in the
tree (and for `RANGE_*` must lie inside the inclusive range used by the
scenario; for `PREFIX_FIRST` they must share the prefix used by the scenario).

---

## 2. Module table

Files are loaded in the order listed. Only `main.aura` may print to stdout.

| # | File             | Required exported forms (API)                                                                                                       |
|---|------------------|-------------------------------------------------------------------------------------------------------------------------------------|
| 1 | `types.aura`     | `(define key=? a b)`, `(define key<? a b)`, `(define make-version txid ts)`, `(define version-visible? v reader-txid)`              |
| 2 | `codec.aura`     | `(define (encode-key s))`, `(define (decode-key s))`, `(define (prefix-compress prev cur))`, `(define (prefix-restore prev cur))`   |
| 3 | `leaf.aura`      | `(define (make-leaf capacity))`, `(define (leaf-insert! leaf k pk v))`, `(define (leaf-split! leaf))`, `(define (leaf-range leaf lo hi))`, `(define (leaf-first-key leaf))`, `(define (leaf-last-key leaf))`, `(define (leaf-bytes leaf))` |
| 4 | `node.aura`      | `(define (make-node leaf? capacity))`, `(define (node-is-leaf? n))`, `(define (node-insert! n k pk v))`, `(define (node-split! n))`, `(define (node-find-child n k))`, `(define (node-key-at n i))`, `(define (node-count n))` |
| 5 | `tree.aura`      | `(define (make-tree order))`, `(define (tree-insert! t k pk v))`, `(define (tree-point t k))`, `(define (tree-range t lo hi))`, `(define (tree-prefix t p))`, `(define (tree-height t))`, `(define (tree-stats t))` |
| 6 | `mvcc.aura`      | `(define (mvcc-choose vlist reader-txid))`, `(define (mvcc-count-visible t reader-txid))`, `(define (mvcc-count-hidden t reader-txid))` |
| 7 | `scan.aura`      | `(define (range-scan t lo hi))`, `(define (prefix-scan t p))`, `(define (scan-count s))`, `(define (scan-first s))`, `(define (scan-last s))` |
| 8 | `metrics.aura`   | `(define (metrics-new))`, `(define (metrics-on-insert! m split?))`, `(define (metrics-nodes m))`, `(define (metrics-inserts m))`, `(define (metrics-bytes-delta! m comp raw))` |
| 9 | `events.aura`    | `(define (event-log-new))`, `(define (event-log-add! log k pk v))`, `(define (event-log-replay log))`, `(define (event-log-count log))` |
| 10| `index.aura`     | `(define (make-index order))`, `(define (index-insert! ix k pk v))`, `(define (index-point ix k reader-txid))`, `(define (index-range ix lo hi))`, `(define (index-prefix ix p))`, `(define (index-mvcc-stats ix reader-txid))`, `(define (index-height ix))`, `(define (index-stats ix))`, `(define (index-bytes ix))` |
| 11| `main.aura`      | scenario driver; uses APIs from files 1–10; prints the 14 KEY=value lines   |

`order` is a small integer fanout (e.g. 4). The exact value is up to the
implementation; the grader only checks the 14 stdout keys.

---

## 3. Scenario steps (executed by `main.aura`)

All steps below must call into the module APIs above; `main.aura` itself only
orchestrates and prints.

1. `(define ix (index-make 4))` — make a fresh index with fanout 4.
2. Build a list `seed` of 12 records of the shape `(key primary-key version)`,
   where keys are `"user:00007"` … `"user:00042"` (zero-padded to 5 digits),
   primary keys are `"p0"` … `"p11"`, and each version is `(make-version 1 i)`
   for `i` in `0..11`. The order of insertion in the seed list MUST be
   out-of-order on purpose (e.g. 7, 17, 37, 12, 42, 22, 27, 2, 32, 47, 52, 57)
   so the B-tree actually splits.
3. Fold `seed` with `(index-insert! ix k pk v)`. After each successful insert,
   push the inserted key onto a local list `inserted`.
4. Read `(index-stats ix)` to obtain `(nodes inserts)`. Print
   `KEYS_INSERTED=inserts` and `NODES_CREATED=nodes`.
5. Print `TREE_HEIGHT=<index-height ix>`.
6. Do `(define hits (index-point ix "user:00022" 99))` and
   `(define miss (index-point ix "user:99999" 99))`. Both return
   `(visible . pk-or-#f)` pairs. Print `POINT_HIT=<cdr of hit>` (expected `2`)
   and `POINT_MISS=0` if `miss` returned `#f` else `POINT_MISS=1` (scenario
   guarantees miss).
7. Do `(define rs (index-range ix "user:00010" "user:00050"))`. Use
   `scan-count`, `scan-first`, `scan-last` to obtain count and boundary keys.
   Print `RANGE_COUNT=<scan-count rs>`,
   `RANGE_FIRST=<scan-first rs>`, `RANGE_LAST=<scan-last rs>`.
8. Do `(define ps (index-prefix ix "user:000"))`. Print
   `PREFIX_COUNT=<scan-count ps>`, `PREFIX_FIRST=<scan-first ps>`.
9. Replay-style MVCC: for reader-txid `100`, call
   `(index-mvcc-stats ix 100)`. It must walk every leaf and use
   `mvcc-choose`/`version-visible?` to count visible vs hidden entries (older
   versions are considered hidden when a newer committed version exists in the
   same leaf; the grading data guarantees exactly 3 visible / 2 hidden for
   this seed). Print `MVCC_VISIBLE=<v>` and `MVCC_HIDDEN=<h>`.
10. Ask the index for byte statistics: `(index-bytes ix)` returns
    `(compressed . raw)`. Print `COMPRESS_BYTES=<compressed>`,
    `RAW_BYTES=<raw>`.
11. As a final touch, append every record from `inserted` into an
    `event-log`, then call `(event-log-replay log)` to rebuild a second index
    `ix2`. The replay must produce the same counts; main does NOT print those
    counts (they are internal), only asserts `equal?` on the boundary keys
    before exiting.

`main.aura` must not contain any literal that matches the expected stdout
values; every number/string printed must come from a return value of one of
the module APIs above. (Anti-hardcode rule.)

---

## 4. Anti-hardcode rules

- `main.aura` must not contain the literal strings `user:00022`, `user:99999`,
  `user:00010`, `user:00050`, `user:00007`, `user:00042` *outside* of the
  seed-data list. In particular, the literal `user:00022` used for `POINT_HIT`
  must be passed *into* `index-point` from a list variable.
- All 14 printed values must originate from API return values. No
  `(display "TREE_HEIGHT=3")`-style shortcuts. The grader will rewrite the
  seed ordering; the printed numbers/strings must change accordingly.
- Each `.aura` file in §2 must `define` every API listed for it. The grader
  greps for those names.

---

## 5. How to run



Exit code `0` is expected on success. The grader reads stdout, splits on `\n`,
keeps only lines matching `^[A-Z_]+=-?\d+$` or `^[A-Z_]+=.+$`, and compares
against the 14 keys above in order.
