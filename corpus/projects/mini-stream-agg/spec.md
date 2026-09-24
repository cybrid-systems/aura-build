# Streaming Aggregation Engine — mini-stream-agg

A toy in-memory **streaming aggregation engine** written in Aura (Lisp-like). It demonstrates the four hard parts of a real stream aggregator:

1. **Grouped aggregation** keyed by a tuple of fields (here just `(user-id)`), with incremental `+ retract` semantics.
2. **State-tier promotion** — hot records live in a fast hashmap tier; once a key is touched too often it gets promoted to a "rocks-like" sorted tier; once too large, it spills to an overflow tier. Each tier implements the same `tier-step` interface.
3. **Exactly-once checkpointing** — every N events the engine snapshots the world state, and a `recovery` step proves that a replayed prefix produces the identical state and identical outputs.
4. **Watermark / late events** — events arriving after the watermark can still retract cleanly thanks to the retract log.

The engine is deliberately small (3 backing tiers × 1 agg function × 1 key), but the *shape* is what a production mini-batch stream job looks like.

## Stdout contract

The program prints exactly these KEY=value lines, in this order, on a single invocation:



(`EVENTS_PROCESSED` must equal the number of input events fed to `engine-step`; `REPLAY_MATCH` must be `#t`; all numbers are non-negative integers; `END_STATE_HASH` is a hex string.)

## Module table

| File | Required exported `(define (api …) …)` forms |
|------|---------------------------------------------|
| `event.aura` | `(api event-make user-id delta ts)`, `(api event? x)`, `(api event-user-id e)`, `(api event-delta e)`, `(api event-ts e)` |
| `tier.aura` | `(api tier-make kind)`, `(api tier-step t k delta)`, `(api tier-get t k)`, `(api tier-keys t)`, `(api tier-size t)`, `(api tier-promote? t k)` |
| `tier-hashmap.aura` | `(api hashmap-tier-new)` — returns a tier of kind `'hashmap` |
| `tier-sorted.aura` | `(api sorted-tier-new)` — returns a tier of kind `'sorted` |
| `tier-overflow.aura` | `(api overflow-tier-new cap)` — returns a tier of kind `'overflow` capped at `cap` |
| `aggregator.aura` | `(api agg-make)`, `(api agg-step agg k delta ts)`, `(api agg-final agg k)` — sum/count aggregator with retract-safe state |
| `watermark.aura` | `(api wm-advance wm ts)`, `(api wm-is-late? wm ts)`, `(api wm-current wm)` |
| `checkpoint.aura` | `(api ckpt-snapshot state)`, `(api ckpt-restore snap)`, `(api ckpt-hash state)` |
| `recovery.aura` | `(api recovery-replay events checkpoints)` returns `(values replay-state match?)` |
| `metrics.aura` | `(api metrics-record m tier kind key)`, `(api metrics-snapshot m)` |
| `engine.aura` | `(api engine-new)`, `(api engine-step eng event)`, `(api engine-flush eng)`, `(api engine-stats eng)`, `(api engine-tier-counts eng)`, `(api engine-promotions eng)`, `(api engine-demotions eng)`, `(api engine-checkpoint eng)` |
| `demo-events.aura` | `(api demo-events-build)` — returns the deterministic event list used by the scenario |
| `hash.aura` | `(api hash-fold n)` — tiny FNV-1a-ish integer fold used for `END_STATE_HASH` |
| `main.aura` | scenario driver; consumes all module APIs above |

## Scenario steps (main.aura only)

`main.aura` performs these steps and only prints after step 6:

1. Build the deterministic event stream via `(demo-events-build)`.
2. Construct an engine with `(engine-new)`.
3. For each event `e` in the stream: call `(engine-step eng e)`; on every 5th event also call `(engine-checkpoint eng)`.
4. Call `(engine-flush eng)`.
5. Call `(recovery-replay events checkpoints)` using the event stream and the checkpoints accumulated in step 3.
6. Collect stats via `(engine-stats eng)`, tier counts via `(engine-tier-counts eng)`, and replay-match via the second return value of `recovery-replay`.
7. Print all `KEY=value` lines in the exact order above using the API-returned values (never literal numbers).
8. Assert `REPLAY_MATCH` is `#t`; abort with a non-zero exit if not (display `REPLAY_MISMATCH` and exit).

## Anti-hardcode

`main.aura` must not embed magic numbers for `EVENTS_PROCESSED`, `FINAL_USER_SUM`, `FINAL_USER_COUNT`, tier sizes, or the replay-match boolean. Every printed value must come from a module API call (`engine-stats`, `engine-tier-counts`, `recovery-replay`, `ckpt-hash`, etc.). The event stream itself comes from `(demo-events-build)` so the *scenario* is reproducible without hardcoding the answer into `main`.

## How to run

```sh
aura event.aura tier.aura tier-hashmap.aura tier-sorted.aura tier-overflow.aura \
     aggregator.aura watermark.aura checkpoint.aura recovery.aura metrics.aura \
     hash.aura engine.aura demo-events.aura main.aura
json dogfood
{"files":["event.aura","tier.aura","tier-hashmap.aura","tier-sorted.aura","tier-overflow.aura","aggregator.aura","watermark.aura","checkpoint.aura","recovery.aura","metrics.aura","hash.aura","engine.aura","demo-events.aura","main.aura"],"entry":"main.aura","run_mode":"cli_multi","expect_keys":["ENGINE_NAME","EVENTS_PROCESSED","ACCEPTS","RETractS","FINAL_USER_SUM","FINAL_USER_COUNT","FINAL_DISTINCT_USERS","HOT_TIER_KEYS","SORTED_TIER_KEYS","OVERFLOW_TIER_KEYS","PROMOTIONS","DEMOTIONS","CHECKPOINT_EPOCHS","REPLAY_MATCH","END_STATE_HASH"],"source_res":["\\(define\\s+\\(event-make\\b","\\(define\\s+\\(tier-make\\b","\\(define\\s+\\(hashmap-tier-new\\b","\\(define\\s+\\(sorted-tier-new\\b","\\(define\\s+\\(overflow-tier-new\\b","\\(define\\s+\\(agg-make\\b","\\(define\\s+\\(wm-advance\\b","\\(define\\s+\\(ckpt-snapshot\\b","\\(define\\s+\\(recovery-replay\\b","\\(define\\s+\\(metrics-record\\b","\\(define\\s+\\(engine-new\\b","\\(define\\s+\\(demo-events-build\\b","\\(define\\s+\\(hash-fold\\b","\\(define\\s+\\(main\\b"]}
```
