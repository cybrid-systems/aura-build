```markdown
# mini-wal-btree-page — Goal

A small, in-memory **Write-Ahead Log + page-oriented B+tree** engine implemented in Aura.
Pages are fixed-size byte-blobs (we model them as lists of cells), writes go to a WAL
before reaching the page cache, splits/merges propagate under LSN ordering, and a
recovery walk replays the WAL using LSN-pinned redo/undo to reach a consistent state.

The goal is a clean separation between **log framing**, **page cache**, and **B+tree
operations**, so every layer can be exercised from `main.aura` and verified by its
`stdout` contract (no hard-coded literals — every number printed is computed by the
APIs).

---

## 1. Exact `stdout` contract

`main.aura` prints exactly these KEY=value lines, in this order, each terminated by
`\n`. Values are computed by the APIs, never embedded as literals.



(Count of keys is `16`. `main.aura` aborts with a non-zero `display` exit code if any
expected key is missing or out of order — the contract is positional.)

---

## 2. Module / API table

Loaded left-to-right by the Aura CLI. Each file contributes the listed `define`s on
the shared top-level. The last file (`main.aura`) drives the scenario and prints the
contract above.

| # | File | Required top-level forms |
|---|------|--------------------------|
| 1 | `constants.aura` | `(define PAGE_ORDER 4)`, `(define PAGE_BYTES 128)`, `(define WAL_MAGIC_STR "WAL1")`, `(define LSN_START 1)`, `(define MAX_CELLS_PER_PAGE ...)` |
| 2 | `util.aura` | `(define (u16 x) ...)`, `(define (u8 x) ...)`, `(define (crc16 xs) ...)`, `(define (bytes=? a b) ...)`, `(define (take n xs) ...)`, `(define (drop n xs) ...)` |
| 3 | `lsn.aura` | `(define (lsn-next l) ...)`, `(define (lsn<? a b) ...)`, `(define (lsn-equal? a b) ...)`, `(define (lsn-max a b) ...)`, `(define (make-lsn-seq from) ...)` |
| 4 | `wal.aura` | `(define (wal-open magic) ...)`, `(define (wal-append wal frame) ...)`, `(define (wal-truncate-before wal lsn) ...)`, `(define (wal-frames wal) ...)`, `(define (wal-frame-lsn f) ...)`, `(define (wal-frame-payload f) ...)`, `(define (wal-rewrite wal lsn payload) ...)` |
| 5 | `page.aura` | `(define (page-empty pid) ...)`, `(define (page-id p) ...)`, `(define (page-cells p) ...)`, `(define (page-set-cells p cs) ...)`, `(define (page-lsn p) ...)`, `(define (page-set-lsn! p lsn) ...)`, `(define (page-full? p) ...)`, `(define (page-split p new-pid) ...)`, `(define (page-merge a b) ...)`, `(define (page-crc p) ...)` |
| 6 | `cache.aura` | `(define (cache-new) ...)`, `(define (cache-get c pid) ...)`, `(define (cache-put! c pid page) ...)`, `(define (cache-evict c pid) ...)`, `(define (cache-dirty-ids c) ...)`, `(define (cache-flush! c wal) ...)` |
| 7 | `btree.aura` | `(define (btree-open) ...)`, `(define (btree-put! tree key val wal cache) ...)`, `(define (btree-delete! tree key wal cache) ...)`, `(define (btree-get tree key) ...)`, `(define (btree-root tree) ...)`, `(define (btree-root-key tree) ...)`, `(define (btree-stats tree) ...)` |
| 8 | `codec.aura` | `(define (encode-cell k v) ...)`, `(define (decode-cell xs) ...)`, `(define (encode-skip key) ...)`, `(define (encode-delete key) ...)` |
| 9 | `txn.aura` | `(define (txn-begin lsn) ...)`, `(define (txn-commit! txn wal) ...)`, `(define (txn-abort! txn wal) ...)`, `(define (txn-redo txn) ...)`, `(define (txn-undo txn) ...)` |
| 10 | `recovery.aura` | `(define (recover wal cache tree) ...)`, `(define (redo-wal-into! wal cache) ...)`, `(define (undo-before! wal lsn cache) ...)`, `(define (recovery-summary r) ...)` |
| 11 | `stats.aura` | `(define (stats-new) ...)`, `(define (stats-bump-puts! s) ...)`, `(define (stats-bump-splits! s) ...)`, `(define (stats-bump-merges! s) ...)`, `(define (stats-bump-deletes! s) ...)`, `(define (stats-bump-redo! s) ...)`, `(define (stats-bump-undo! s) ...)`, `(define (stats-snapshot s) ...)` |
| 12 | `hex.aura` | `(define (hex-encode n) ...)`, `(define (hex-decode s) ...)` |
| 13 | `logscan.aura` | `(define (log-scan wal from-lsn) ...)`, `(define (log-frame-count wal) ...)` |
| 14 | `main.aura` | scenario driver (see §4) — no API exported |

> `main.aura` is the only file allowed to call `(display …)` and `(newline)`.

---

## 3. Scenario steps (executed by `main.aura`)

The driver must run **only** through the APIs in §2. The exact sequence:

1. **Boot**: call `wal-open` with `WAL_MAGIC`; call `cache-new`; call `btree-open`.
2. **Inserts (8 keys)**: call `btree-put!` for each `(key 10 7)` in the keys list produced
   by walking the keys stream — values vary so CRC differs. After every insert,
   `txn-begin` → frame write via `wal-append` (LSN advanced through
   `lsn-next`) → `page-set-lsn!` updates the page → `txn-commit!` flushes through
   `cache-flush!`.
3. **Splits**: when `page-full?` is true during insert, `page-split` is invoked by
   `btree-put!`. Count splits via `stats-bump-splits!`. After two forced full
   splits, the running total is `2`.
4. **Deletes (3 keys)**: `btree-delete!` on the first three inserted keys; each
   delete bumps `stats-bump-deletes!`. No page underflows → `MERGES=0`.
5. **Crash simulation**: evict the root page via `cache-evict` so that the next read
   must rebuild from the WAL. Do *not* truncate.
6. **Recovery**: call `recover` which internally runs `redo-wal-into!` (LSN-pinned
   forward scan starting at `LSN_START`) and `undo-before!` for any open/aborted
   frames. `recovery-summary` returns redo/undo counts.
7. **Read-back**: call `btree-get` for the median surviving key to compute
   `RECOVERED_ROOT_KEY`.
8. **Integrity**: walk every cached page and call `page-crc`; aggregate with
   `(and …)` over `(equal? … #t)` results to produce `CRC_OK` (1 = ok, 0 = bad).
9. **Stats + WAL counters**: `stats-snapshot` → puts/splits/merges/deletes/redo/undo;
   `log-frame-count` → `LOG_FRAMES`; wal frames list length also rechecked against
   the same counter for parity.
10. **Print contract**: emit the 16 `KEY=value` lines from §1, each obtained from the
    API results — `TREE_ORDER` from `PAGE_ORDER`, `PAGE_BYTES` from `PAGE_BYTES`,
    `WAL_MAGIC` from `WAL_MAGIC_STR`, `LSN_START` from `LSN_START`, `RECOVERED_ROOT_KEY`
    from the read-back in step 7, etc.

### Anti-hardcode guard

The contract values are not literals. Concretely:

* `SPLITS=2` is only true if `page-split` was actually invoked by `btree-put!` for
  two inserts — the count is read from `stats-snapshot`.
* `MERGES=0` is computed by counting `page-merge` calls; a hardcoded `0` would fail
  if the workload were rerun with different keys.
* `RECOVERED_ROOT_KEY` is the result of `btree-get` — changing the input key stream
  changes the printed median.
* `CRC_OK` is the conjunction of `page-crc` over every live page, not a constant.
* `LOG_FRAMES` must equal `(length (wal-frames wal))`; both are printed and compared.

A test harness rerunning with a different `(PAGE_ORDER)` or different key stream
must produce a contract whose **only changed values** are `PUTS`, `SPLITS`,
`LOG_FRAMES`, `RECOVERED_ROOT_KEY` (and possibly `REDO_COUNT`), and all of them
must still trace back to an API call.

---

## 4. How to run



Expected stdout (order matters):



(The `RECOVERED_ROOT_KEY` value depends on the key stream chosen by the driver —
the harness measures it dynamically and stores the exact reference value out of
band.)

---

## 5. Design notes / constraints

* **No dicts, no vectors.** Cells, frames, and pages are flat lists.
* **LSN pinning**: `redo-wal-into!` only applies frames whose `lsn-equal?` their
  target page's `page-lsn` would be overwritten by; frames stamped *above* the
  current page LSN are skipped (this is the "LSN-pinned" behavior).
* **Split invariant**: `page-split` returns `(cons new-page old-page)`; both
  pages carry the post-split LSN written via `wal-append` first.
* **Recovery summary**: `recovery-summary` returns an alist
  `((redo . n) (undo . m))`; main converts each to its KEY.
* **CRC**: a tiny CRC-16 over the cell list (XOR + rotate). Bad pages set `CRC_OK`
  to `0`; a healthy store yields `1`.

---

## 6. Source-of-truth regexes (for the grader)

Each regex below must match **at least once** in the concatenated project source
(`cat *.aura`). They pin down that the API names in §2 are real `define`s, not
just calls.
