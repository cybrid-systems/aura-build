# COW-WAL: Copy-on-Write Log-Structured Store

A toy in-memory copy-on-write write-ahead log (WAL) that flushes immutable segments,
keeps a root pointer for indirection, and supports snapshot reads. Demonstrates the
core mechanics of storage systems like LMDB / BoltDB / IceFS without the disk: each
"commit" produces a new immutable segment snapshot, and older snapshots remain
readable via root pointer versioning.

## Stdout contract

The scenario MUST print exactly these KEY=value lines, in this order, no extra output:



## Module table

| File | Required exported `(define (api …))` forms |
|------|---------------------------------------------|
| `segment.aura` | `(make-segment id entries)`, `(segment-id seg)`, `(segment-entries seg)`, `(segment-size seg)` |
| `wal.aura` | `(make-wal)`, `(wal-append wal key value)`, `(wal-commit wal)`, `(wal-active wal)`, `(wal-segments wal)`, `(wal-root wal)`, `(wal-roots wal)`, `(wal-fork wal root-id)`, `(wal-read-at wal root-id key)`, `(wal-keys-at wal root-id)`, `(wal-gc wal keep-roots)` |
| `snapshot.aura` | `(make-snapshot root-id segments)`, `(snapshot-get snap key)`, `(snapshot-keys snap)`, `(snapshot-root-id snap)`, `(snapshot-segment-count snap)` |
| `gc.aura` | `(plan-gc wal keep-roots)`, `(gc-reclaimable-segments wal keep-roots)`, `(run-gc wal keep-roots)` |
| `metrics.aura` | `(make-metrics)`, `(metrics-inc m k)`, `(metrics-get m k)`, `(metrics-snapshot m)` |
| `codec.aura` | `(encode-entry key value)`, `(decode-entry cell)`, `(kv-pair? x)` |
| `root.aura` | `(make-root id parent-id segment-id)`, `(root-id r)`, `(root-parent r)`, `(root-segment r)`, `(root=? a b)` |
| `keydir.aura` | `(make-keydir)`, `(keydir-put kd key offset)`, `(keydir-get kd key)`, `(keydir-snapshot kd)`, `(keydir-entries kd)` |
| `history.aura` | `(history-record hist root-id)`, `(history-list hist)`, `(history-len hist)`, `(history-at hist idx)` |
| `delta.aura` | `(make-delta puts deletes)`, `(delta-apply-to seg)`, `(delta-puts d)`, `(delta-deletes d)`, `(empty-delta?)` |
| `cow.aura` | `(cow-merge base-seg delta)`, `(cow-fork wal at-root)`, `(cow-readable-at wal root-id)` |
| `report.aura` | `(format-kv-list alist)`, `(kvline key value)`, `(print-stats stats)` |
| `main.aura` | (entry point — orchestrates scenario, calls APIs, prints the KEY=… contract) |

## Scenario steps (executed inside `main.aura`)

1. **Bootstrap** — call `(make-wal)` from `wal.aura`; bind to `W`.
2. **Commit 0** — three `wal-append` calls (`alpha=1`, `beta=beta-v0`, `gamma=g0`), then `(wal-commit W)`. Record returned root as `R0`.
3. **Fork at R0** — `(wal-fork W R0)` to obtain an independent handle (not mutated; just demonstrates COW indirection).
4. **Commit 1** — append `alpha=42`, `beta=beta-v1`, `delta=d1`; `(wal-commit W)` → `R1`. Verify `gamma` from R0 is unreachable in active WAL but reachable via `wal-read-at`.
5. **Commit 2** — append `alpha=200`, `beta=beta-stable`; `(wal-commit W)` → `R2`. Active WAL now has R2 as latest.
6. **Root promotion** — manually build an additional root `R3` via `(make-root 'R3 'R2 <seg>)` and register via a tiny helper exported from `wal.aura` (e.g., `(wal-promote W R3)`) so `wal-root` returns `R3`.
7. **Snapshot reads** — for each of R0/R1/R2, build snapshots with `(make-snapshot …)` and use `(snapshot-keys …)` plus `(snapshot-get …)` to verify COW visibility.
8. **GC pass** — `(run-gc W '(R2 R3))` to reclaim segments only referenced by R0/R1. Capture reclaimed count.
9. **Forked-root readability check** — re-read a key via `(wal-read-at W R1 'alpha)` (R1 was forked earlier); confirm result.
10. **History emit** — `(history-list …)` joined into a comma-separated string for the `ROOT_HISTORY` line.
11. **Print contract** — emit all 14 KEY=value lines using values derived from API calls.

## Anti-hardcode

`main.aura` MUST:
- Call `wal-append`, `wal-commit`, `wal-fork`, `wal-read-at`, `wal-keys-at`, `wal-roots`, `wal-root`, `wal-segments`, `wal-gc`, `run-gc`, `make-snapshot`, `snapshot-keys`, `snapshot-get`, `history-list`, `make-root`.
- Derive every printed value from those calls. For example `LATEST_ROOT` is the symbol returned by `(wal-root W)` converted via `symbol->string`; `SNAPn_KEYS` is the `length` of `(snapshot-keys snap)`; `KEY_ALPHA_AFTER_COMMIT2` is `(wal-read-at W R2 'alpha)`.
- It must NOT print literal strings like `"R3"` or `200` without having obtained them from the module APIs in the same run.
- The reuse of the string `"beta-stable"` is acceptable only because that exact value was passed into `wal-append` and read back via `wal-read-at`.

## How to run



All files share a single top-level environment; later files may call any earlier
`define`. `main.aura` is last so its top-level expressions execute after all
modules are loaded.
