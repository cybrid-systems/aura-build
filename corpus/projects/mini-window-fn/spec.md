# GOAL.md — Mini Window Function Runtime

## 1. Overview
A small in-memory query engine that evaluates SQL-style window functions over a relation. Supports `ROW_NUMBER`, `RANK`, `DENSE_RANK`, plain aggregates (`SUM`, `AVG`, `MIN`, `MAX`, `COUNT`) over an explicit `frame`, both `RANGE`-style and `ROWS`-style. Two execution strategies are exposed: a **sort-based** path (full sort then per-partition scan) and a **hash-based** path (spill-light streaming via a per-partition accumulator). Streaming mode is signaled via an explicit `(set! *mode* 'streaming)` flag; the same API works in both modes. All state lives in lists/alists — no hash tables, no records. Pure Aura, ~12 files, single CLI invocation.

## 2. Exact stdout contract
The scenario prints exactly these 16 `KEY=value` lines, in this order, one per line, terminated by a single trailing newline:



## 3. Module table

| File | Required exported `(define (api …))` forms |
|------|---------------------------------------------|
| `types.aura` | `(api wf-rel?), (api wf-row), (api wf-col), (api wf-part-key)` |
| `schema.aura` | `(api wf-make-relation cols rows), (api wf-relation-cols), (api wf-relation-rows)` |
| `partition.aura` | `(api wf-partition rel key-col), (api wf-part-rows part), (api wf-part-key part)` |
| `sort.aura` | `(api wf-sort rows cmp), (api wf-sort-by rows col rel)` |
| `frame.aura` | `(api wf-make-frame kind lo hi), (api wf-frame-string f), (api wf-rows-in-frame rows frame pivot)` |
| `rank.aura` | `(api wf-row-number), (api wf-rank), (api wf-dense-rank), (api wf-apply-rank rows order-col score-col)` |
| `agg.aura` | `(api wf-sum rows col), (api wf-avg rows col), (api wf-min rows col), (api wf-max rows col), (api wf-count rows)` |
| `window-sort.aura` | `(api wf-window-sort rel part-col order-col frame rank-fn)` |
| `window-hash.aura` | `(api wf-window-hash rel part-col frame rank-fn)` |
| `streaming.aura` | `(api wf-streaming-on), (api wf-streaming-off), (api wf-streaming?)` |
| `runner.aura` | `(api wf-run cfg rel)` — dispatches sort vs hash by `*mode*` |
| `main.aura` | (no exports; scenario driver + final `display`) |

## 4. Scenario steps (executed inside `main.aura`)
1. Build a 10-row relation with columns `(Name Department Employee Score Age)` via `wf-make-relation`.
2. Set `*mode*` to `'sort` via `wf-streaming-off` (default).
3. Call `wf-run` with cfg: `part=Department`, `order=Score`, `frame=ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING`, `rank=RANK`. Record `WF_PARTITIONS`, `WF_ROWS`, `WF_SUM_FRAME`, `WF_AVG_FRAME`, `WF_MIN_FRAME`, `WF_MAX_FRAME`, `WF_RANK_Q2`.
4. Call `wf-window-sort` with `rank-fn=ROW_NUMBER` over partition `Department='Q1'`; record `WF_ROW_NUMBER_Q1`.
5. Call `wf-window-sort` with `rank-fn=DENSE_RANK` over partition `Department='Q2'`; record `WF_DENSE_Q2`.
6. Compute `WF_PEER_GROUP`, `WF_RANK_FUNC`, `WF_FRAME` via the type/schema APIs (string round-trip).
7. Verify `WF_STRATEGY` equals the symbol returned by `wf-run`'s strategy probe (`'sort`).
8. Flip mode: `wf-streaming-on` then `wf-run` again on a copy of the relation; assert result equals prior result → `WF_STREAMING_OK=#t`.
9. Re-run the full scenario twice from scratch and compare outputs list-for-list → `WF_DETERMINISTIC=#t`.
10. Set `WF_MODE` to the stringified value of `*mode*` and print all 16 `KEY=value` lines in the exact order above.

## 5. Anti-hardcode guard
`main.aura` MUST:
- Call at least 8 distinct exported APIs across `partition`, `sort`, `frame`, `rank`, `agg`, `window-sort`, `window-hash`, `streaming`, `runner`.
- Derive every numeric `WF_*` value from a `(wf-sum …)` / `(wf-rank …)` / `(wf-row-number …)` call — no literal constants for `WF_SUM_FRAME`, `WF_AVG_FRAME`, `WF_MIN_FRAME`, `WF_MAX_FRAME`, `WF_ROW_NUMBER_Q1`, `WF_RANK_Q2`, `WF_DENSE_Q2`, `WF_PARTITIONS`, `WF_ROWS`.
- Use `wf-frame-string` to compose `WF_FRAME` (no hand-written frame string).
- Use `wf-part-key` / `wf-rel?` to obtain `WF_PEER_GROUP` (no literal "Department").

## 6. How to run
