# mini-exchange — 15-file multi-file success predicate (tier after mini-saga)

Write a **fifteen-file** Aura program that implements a miniature **limit-order
exchange** with cross-module invariants, and prints exactly these lines (each
plus a trailing newline), **in this order**:

```
FILL1=partial
LEFT1=3
RISK=reject
STP=0
CXL=cancelled
HALT=halted
REJ_HALT=reject
RESUME=open
DUP=dup
REPLAY=ok
EQ=1
FEES=14
COUNT=10
```

## Semantics (pure Aura — no Python)

Single symbol. Prices/qtys are integers. Fee = **1 per qty per side** on each fill
(`fee-charge` once per side → 2×qty added to `fee-total` for a fill of qty).

| File | API |
|------|-----|
| `idemp.aura` | `(idemp-init)` `(idemp-seen? key)` `(idemp-mark key)` |
| `journal.aura` | `(journal-init)` `(journal-append kind a b c d e)` → cons `(list kind a b c d e)`; `(journal-all)`; `(journal-oldest-first)` via `reverse` |
| `ledger.aura` | `(ledger-init)` `(ledger-fund acct cash pos)` `(ledger-cash acct)` `(ledger-pos acct)` `(ledger-debit-cash acct n)` `(ledger-credit-cash acct n)` `(ledger-credit-pos acct n)` `(ledger-debit-pos acct n)` |
| `fee.aura` | `(fee-init)` `(fee-rate)`→`1` `(fee-charge n)` `(fee-total)` |
| `risk.aura` | `(risk-check acct side price qty)` → `"ok"`\|`"reject"`. Buy: `cash >= price*qty + fee-rate*qty`. Sell: `pos >= qty`. Also `"reject"` if `price*qty > 500`. |
| `book.aura` | Order=`(list oid acct side price qty seq)`. `(book-init)` `(book-next-seq)` `(book-add oid acct side price qty)` `(book-remove oid)` `(book-find oid)` `(book-qty oid)` `(book-set-qty oid q)` `(book-bids)` `(book-asks)` |
| `match.aura` | `(match-against acct side price qty oid)` → filled qty. Price-time on opposite book; **STP** skips same `acct`. Calls `(settle-fill …)` per fill slice. Does not rest remainder. |
| `settle.aura` | `(settle-init)` `(settle-fill buyer seller price qty)` — fee each side; buyer debit cash+credit pos; seller credit cash−fee + debit pos |
| `halt.aura` | `(halt-init)` `(halt-set s)` `(halt-state)` — `"open"`\|`"halted"` |
| `order.aura` | `(order-init)` `(order-place cloid acct side price qty)` → `"dup"`\|`"reject"`\|`"filled"`\|`"partial"`\|`"resting"` (idemp→halt→risk; on accept mark+journal place+match+rest rem+journal fill). `(order-cancel cloid)` → `"cancelled"`\|`"missing"` |
| `snapshot.aura` | `(snapshot-fp)` fingerprint string of Alice/Bob cash/pos, fees, bid/ask counts, halt |
| `replay.aura` | `(replay-clear-live)` re-init ledger/fee/book/halt/idemp, fund Alice 100/0 Bob 100/10, **keep journal**. `(replay-run)` apply `journal-oldest-first`: `place` re-match+rest (no risk/halt); `cancel` remove; skip `fill`. → `"ok"` |
| `query.aura` | `(query-left oid)` `(query-fp)` `(query-fees)` `(query-halt)` |
| `exchange.aura` | `(exchange-init)` all inits + funds; `(exchange-place …)` `(exchange-cancel …)` `(exchange-halt)` `(exchange-resume)` `(exchange-snapshot)` `(exchange-replay)` `(exchange-eq a b)` → `1`\|`0` |
| `main.aura` | Scenario below — must call exchange/query ops |

## Scenario (`main.aura`)

1. `(exchange-init)` — Alice cash=100 pos=0; Bob cash=100 pos=10
2. `(exchange-place "A1" "Alice" "buy" 5 10)` rests
3. `(exchange-place "B1" "Bob" "sell" 5 7)` fills 7 → Alice left 3
4. `FILL1=` `"partial"` iff `(query-left "A1")` is 3; `LEFT1=` that left qty
5. `(exchange-place "BIG" "Alice" "buy" 9 100)` → `RISK=reject` (notional cap / cash)
6. `(exchange-place "A2" "Alice" "sell" 5 3)` STP vs own bid → 0 fill; `STP=0`
7. `(exchange-cancel "A1")` → `CXL=cancelled`
8. `(exchange-halt)` → `HALT=halted`
9. `(exchange-place "B2" "Bob" "sell" 5 1)` → `REJ_HALT=reject`
10. `(exchange-resume)` → `RESUME=open`
11. `(exchange-place "A1" "Alice" "buy" 5 1)` → `DUP=dup`
12. snap=`(exchange-snapshot)`; `(exchange-replay)` → `REPLAY=ok`; `EQ=` `(exchange-eq snap (exchange-snapshot))` → `1`
13. `FEES=` `(query-fees)` → `14`
14. `COUNT=` number of holds among {FILL1 partial, LEFT1 3, RISK reject, STP 0, CXL cancelled, HALT halted, REJ_HALT reject, RESUME open, DUP dup, EQ 1} → `10`

## Required structure

Defines must live in the named files. Hardcoding all stdout in `main.aura` alone is a fail.

No Python. Prefer `display`/`newline`/`set!`/`equal?`/`=`/`<`/`>`/`+`/`-`/`*`/`if`/`let`/`begin`/`cond`/`and`/`or`/`string-append`/`number->string`/`member`/`cons`/`car`/`cdr`/`null?`/`list`/`reverse`.

## How multi-file runs

```bash
$AURA_BIN idemp.aura journal.aura ledger.aura fee.aura risk.aura book.aura match.aura order.aura settle.aura halt.aura snapshot.aura replay.aura query.aura exchange.aura main.aura
```

## Why stubs start wrong

`stub/*.aura` are intentionally broken so the propose→verify→repair loop has real 15-file work.
