# Mini-Orderbook Matching Engine (GOAL.md)

## 1. Overview

A pure-Aura toy **limit order book** with classic price-time priority matching. The engine
ingests a tape of orders (`NEW`, `CANCEL`, `MODIFY`), produces trades when a marketable
order crosses the spread, partially fills what it can, rests the remainder, and supports
cancels by order id. After processing all events the engine replays the trade tape so the
scenario can observe price/volume statistics computed from actual matches — not hard-coded.

The whole thing runs **in-memory** with association lists (`alists`) and plain lists. No
records, no hash tables, no vectors.

## 2. Stdout Contract

The scenario (`main.aura`) MUST print exactly these `KEY=value` lines, in this order,
on a single successful run:



(15 keys. Values are illustrative targets for a reference input; a correct engine run
on the same deterministic input will reproduce them exactly.)

## 3. Module Table (16 `.aura` files, loaded in order, `main.aura` last)

| # | File | Required public API |
|---|---|---|
| 1 | `event.aura` | `(make-event type side price qty id)` , `(event-type e)`, `(event-side e)`, `(event-price e)`, `(event-qty e)`, `(event-id e)` |
| 2 | `tape.aura` | `(parse-line line)` → list of event objects; `(build-tape lines)` → list |
| 3 | `book.aura` | `(make-book ticker)` , `(book-ticker b)`, `(empty-book? b)`, `(book-buyers b)`, `(book-sellers b)` |
| 4 | `book_ops.aura` | `(add-resting book side price qty id)` → `book`, `(top-bid book)` `(top-ask book)` `(best-bid book)` `(best-ask book)` |
| 5 | `idmap.aura` | `(make-idmap)` , `(idmap-register m id)` , `(idmap-remove m id)` , `(idmap-has? m id)` , `(idmap-count m)` |
| 6 | `queue.aura` | `(make-q)` , `(enqueue q elem)` , `(dequeue q)` → elem-or-#f, `(queue-size q)` |
| 7 | `match.aura` | `(match-order book idmap trade-tape incoming)` → `(values new-book new-idmap new-trade-tape filled-qty open-qty)` |
| 8 | `cancel.aura` | `(cancel-order book idmap id)` → `(values new-book new-idmap cancelled? bool)` |
| 9 | `trade.aura` | `(make-trade taker-id maker-id price qty)` , `(trade-price t)`, `(trade-qty t)`, `(trade-notional t)` |
| 10 | `tape_out.aura` | `(trade->line t)` → string, `(render-trades trades)` → single newline-joined string |
| 11 | `stats.aura` | `(total-volume trades)` `(total-notional trades)` `(vwap trades)` |
| 12 | `book_view.aura` | `(format-top-level book)` → string like `"49x3  |  51x2"` |
| 13 | `counters.aura` | `(make-counters)` , `(bump-new! c)` `(bump-cancel! c)` `(bump-filled! c)` `(bump-resting! c)` ... + `(counter-value c key)` |
| 14 | `engine.aura` | `(run-engine ticker events)` → `(values final-book final-idmap trade-tape counters)` |
| 15 | `scenario.aura` | `(scenario-events)` → deterministic list of event strings / parsed events |
| 16 | `main.aura` | Orchestrates the run and prints the 15 `KEY=value` lines (see §4) |

## 4. Scenario steps (executed only inside `main.aura`)

1. Load `scenario.aura` and call `(scenario-events)` to obtain a deterministic list of
   tape events (mix of `NEW BUY`, `NEW SELL`, `CANCEL`, partial-fills forcing trades).
2. Build the book with `(make-book "AURA")` and a fresh `idmap`, `counters`, trade-tape.
3. `(run-engine ticker events)` — engine loops events through `match.aura` /
   `cancel.aura` / `book_ops.aura`, returning final state.
4. Compute statistics by calling `stats.aura` on the returned trade-tape.
5. Render top-of-book via `book_view.aura`.
6. Read counter values via `counters.aura`.
7. `display` each `KEY=value` line in the exact contract order, then `(newline)`.

## 5. Anti-Hardcode Rules

* `main.aura` MUST obtain every printed value through a public API from modules 1–15.
  No literal numbers or strings like `"49"`, `"42"`, `"1138"` may appear in `main.aura`.
* The expected `KEY=…` lines are produced **only after** `run-engine` returns and
  module APIs compute them from the live in-memory book + trade tape.
* The reference input tape in `scenario.aura` is allowed to be a literal list (it's
  data, not output) — but it MUST be replayed through the matching engine.
* `VWAP`, `TRADE_NOTIONAL`, `BEST_BID_*`, `TOP_LEVEL` are derived outputs, not constants.

## 6. How to Run



Expected exit code `0`. Output is the 15 `KEY=value` lines in §2.
