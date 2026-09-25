```markdown
# Trade Allocation FIFO Ledger (mini-trade-allocation-fifo)

## Overview
A toy in-memory ledger that ingests executed **block trades** on an instrument and
**allocates fills to client tax-lots** under selectable policies (**FIFO**, **LIFO**,
**HIFO**) with **wash-sale tracking** and **lot reassignment**. The scenario builds
the ledger from a small stream of block fills and client tax-lots, runs each policy,
records remaining-lot quantities, realized P&L, wash-sale flags, and reassignment
chains, then prints a fixed `KEY=value` summary. All state lives in lists / alists.

## Exact stdout contract
The scenario `main.aura` must `display` exactly these `KEY=value` lines, in this
order, one per line, terminated by `(newline)` after each. Values are computed by
calling module APIs (no hardcoded literals in `main.aura`).



(`...` denotes values that are computed at runtime; the JSON dogfood at the bottom
lists the keys whose values are verified by a Python reference.)

## Module table

| File | Required exported `define (api …)` forms |
|------|-------------------------------------------|
| `util.aura` | `(api now-tick)` `(api fmt-money n)` `(api round2 n)` |
| `lot.aura` | `(api make-lot client qty cost basis-date)` `(api lot-qty l)` `(api lot-cost l)` `(api lot-client l)` `(api lot-date l)` `(api lot-decrease l qty)` `(api lot-set-qty l qty)` `(api lots-by-client lots client)` `(api lots-total-qty lots)` |
| `block.aura` | `(api make-block id instr side qty price ts)` `(api block-qty b)` `(api block-price b)` `(api block-side b)` `(api block-instr b)` `(api block-ts b)` `(api block-id b)` |
| `ledger.aura` | `(api make-ledger)` `(api ledger-add-lot led lot)` `(api ledger-add-block led blk)` `(api ledger-lots led)` `(api ledger-blocks led)` `(api ledger-tick led)` `(api ledger-bump led)` |
| `policy.aura` | `(api policy-name p)` `(api allocate led block policy)` — returns list of fill records `((client lot-id qty price cost-basis realized) ...)`; policy is one of `'FIFO`, `'LIFO`, `'HIFO` |
| `pnl.aura` | `(api realized-pnl fills)` `(api wash-flags fills ledger)` `(api flag-wash fill ledger)` |
| `reassign.aura` | `(api reassign-ledger led from-client to-client lots)` — moves remaining lots from `from-client` to `to-client` and records a reassignment chain |
| `report.aura` | `(api count-open-lots led)` `(api count-fills fills)` `(api total-pnl fills)` `(api count-wash flags)` `(api count-reassigned ledger)` `(api ledger-ticks led)` `(api summarize led blocks fills-fifo fills-lifo fills-hifo pnl-fifo pnl-lifo pnl-hifo wash)` |
| `main.aura` | orchestrates the demo, calls every API above, and prints the 14 stdout keys |

## Scenario steps (executed by main.aura)
1. `(require` or just rely on shared top-level) load order: `util.aura → lot.aura → block.aura → ledger.aura → policy.aura → pnl.aura → reassign.aura → report.aura → main.aura`.
2. Build a ledger via `(api make-ledger)` and add 4 clients' tax-lots on instrument `ACME` with mixed cost bases and dates.
3. Add 3 block trades on `ACME` at successive timestamps (buy, sell, sell) using `(api make-block)` and `(api ledger-add-block)`.
4. For each block, run `(api allocate led block 'FIFO)`, `'LIFO`, `'HIFO` and collect the resulting fill lists.
5. Bump the ledger tick after each block via `(api ledger-bump led)`.
6. Compute per-policy P&L with `(api realized-pnl fills)`, wash-sale flags with `(api wash-flags fills ledger)`, and reassignment count after `(api reassign-ledger led 'C1 'C2 remaining-lots)`.
7. Call `(api summarize led blocks fills-fifo fills-lifo fills-hifo pnl-fifo pnl-lifo pnl-hifo wash)` and `display` each `KEY=value` line.
8. Print `LEDGER_TICKS` from `(api ledger-ticks led)`.

## Anti-hardcode
`main.aura` must build lots/blocks from `make-lot`/`make-block`, allocate via
`policy/allocate`, derive every numeric key from `pnl.realized-pnl`,
`report.count-open-lots`, `report.count-wash`, `report.count-reassigned`, and
`ledger-tick`. A reference solution that skips any of the module APIs and prints
the expected numbers as literals will fail verification — the run harness checks
that values are reproducible from the API outputs on randomized cost/price
streams.

## How to run


## Implementation notes
- Lots, blocks, and fill records are plain association lists `(list 'client … 'qty … …)`.
- `policy/allocate` walks the lot list in the chosen order and consumes `qty` greedily, returning one fill record per consumed lot slice.
- `pnl/flag-wash` flags a fill when a lot is partially or fully consumed within `30` ticks of a same-instrument opposite-side block on the same client.
- `reassign/reassign-ledger` rewrites the `client` field on remaining open lots and pushes a `(from to lot-id tick)` tuple onto the ledger's reassignment chain.
- `report/summarize` is the only function allowed to format the human-readable `KEY=value` lines; `main.aura` simply `display`s them.
