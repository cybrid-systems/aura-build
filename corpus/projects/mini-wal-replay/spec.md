# WAL Record Replay Engine

A miniature Write-Ahead Log (WAL) replay engine written in Aura. The system stores log records as a list, supports appending inserts and deletes with sequence numbers, and reconstructs the authoritative in-memory state by replaying records from a chosen checkpoint. Record application is idempotent (re-inserts of an already-present key are no-ops, and deletes of absent keys are no-ops). After replay, the engine reports counts and a small sample of state.

## Stdout contract (KEY=value lines, in this exact order)



(10 lines, 10 keys; 8–16 allowed range.)

## Module table (11 files, last is main.aura)

| File | Required `(define (api …))` forms |
|------|-----------------------------------|
| `wal_record.aura` | `(api make-record kind key value seq)`, `(api record? r)`, `(api record-seq r)`, `(api record-kind r)`, `(api record-key r)`, `(api record-value r)` |
| `wal_log.aura` | `(api empty-log)`, `(api log-append log rec)`, `(api log-length log)`, `(api log-ref log i)`, `(api log-all log)` |
| `wal_apply.aura` | `(api apply-record state rec)`, `(api apply-all state log)`, `(api count-applies)` |
| `wal_idempotent.aura` | `(api already-applied? rec)`, `(api mark-applied! rec)`, `(api applied-list)` |
| `wal_replay.aura` | `(api replay-state state log checkpoint-seek)`, `(api replay-count)`, `(api reset-replay-count!)` |
| `wal_state.aura` | `(api empty-state)`, `(api state-set! state k v)`, `(api state-delete! state k)`, `(api state-has? state k)`, `(api state-get state k)`, `(api state-keys state)`, `(api state-count state)` |
| `wal_checkpoint.aura` | `(api checkpoint log seq)`, `(api checkpoint-seq log)` |
| `wal_collect.aura` | `(api collect-keys state)`, `(api collect-values state)` |
| `wal_metrics.aura` | `(api inc-metric! name)`, `(api get-metric name)`, `(api reset-metrics!)` |
| `wal_report.aura` | `(api format-stats counts distinct-keys final-keys replays dropped idempotent sum ticks)` |
| `main.aura` | top-level orchestration; only file that prints |

## Scenario steps (executed in `main.aura`)

1. Build an empty state via `empty-state`, an empty log via `empty-log`, and an empty applied-list via `mark-applied!` reset path.
2. Append 10 records using `log-append` + `make-record`. Use kinds `'insert` and `'delete`, with deliberate **idempotent duplicates** of seqs (one already-present key re-inserted, one already-absent key re-deleted).
3. Set a checkpoint at seq=3 via `checkpoint`.
4. Replay from checkpoint-seq using `replay-state`, which invokes `apply-record` for each record. `apply-record` consults `already-applied?` and calls `mark-applied!`; increments `count-applies` and the `WAL_IDEMPOTENT_APPLIES` / `WAL_REPLAYED` metrics.
5. Compute distinct keys via `state-keys` then `collect-keys`; sort the small key set lexicographically.
6. Sum all numeric values currently present in state via `state-get` + `collect-values`.
7. Count dropped-old (records with `seq <= checkpoint-seq` that appear before the checkpoint cursor) via a tail scan.
8. Tick-based replay-time via a simple deterministic `(for-each …)` loop counter stored through `wal_metrics`.
9. Print the 10 `KEY=value` lines exactly, all values derived from API calls — no hardcoded numbers.

## Anti-hardcode

`main.aura` must compute every printed number by calling module APIs. Concretely:

- `WAL_RECORDS_TOTAL` comes from `(log-length (log-all log))` after appending.
- `WAL_CHECKPOINT_SEQ` comes from `(api-checkpoint-seq …)` after `(api-checkpoint …)`.
- `WAL_DISTINCT_KEYS` comes from `(state-count state)` after replay.
- `WAL_FINAL_KEYS` is built by joining `(state-keys state)` with `","` — never written as a string literal.
- `WAL_IDEMPOTENT_APPLIES` comes from `(get-metric "idempotent")` plus `(applied-list)` length.
- `WAL_REPLAYED` comes from `(get-metric "replayed")`.
- `WAL_DROPPED_OLD` comes from the tail-scan filter over `(log-all log)` using `checkpoint-seq`.
- `WAL_VALUE_SUM` is a `let`/`fold`-style recursion over state values.
- `WAL_REPLAY_TIME_TICKS` is a counter incremented inside the replay loop.
- `WAL_DETERMINISTIC=true` because replay always converges to the same state from the same log.

If the implementation is correct, removing or skipping any module API call should change at least one printed line — proving the output is *computed*, not stored.

## How to run



All files share one top-level environment; `main.aura` is last and is the only file containing `display` / `newline`.
