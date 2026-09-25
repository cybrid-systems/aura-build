```markdown
# Mini OMS Child-Order Slicer

A toy in-memory **Order Management System (OMS)** that takes a parent order, slices it into child orders using common execution strategies (`POV`, `TWAP`, `VWAP`, `liquidity-seeking`), simulates venue routing/fills, monitors completion risk, and finally **allocates fills back to investor accounts** via `FIFO`, `pro-rata`, or `filled-quantity` rules.

The Aura CLI is invoked once with all 16 `.aura` files in order; `main.aura` runs the scenario and prints a single stdout contract of `KEY=value` lines.

---

## 1. Stdout Contract (exact order)

The scenario MUST print exactly these 16 lines (one per line), in this order, using `display` + `newline`. Values are computed at runtime from module APIs — **never hardcoded**.



`ALLOC_CHECKSUM` is `OK` when the sum of per-account allocations equals `ALLOC_TOTAL_FILLED`; otherwise `FAIL`. Numbers are printed with exactly the digits shown (use `number->string` + padding helpers; no rounding mode surprises).

---

## 2. Module Table (16 files, loaded in order)

Each module defines a small set of public `(define (api-…) …)` procedures over plain lists / alists. Internals stay private with `let`/`define` helpers. **No records, no hash tables, no vectors.**

| # | File | Required API exports |
|---|------|---------------------|
| 1 | `util.aura` | `(api-round2 n)`, `(api-pad-right s n)`, `(api-now-tick)` |
| 2 | `market-clock.aura` | `(api-trading-day?)`, `(api-slot-count horizon-secs slot-secs)` |
| 3 | `venue-registry.aura` | `(api-venue-list)`, `(api-venue-fee venue)`, `(api-venue-latency venue)` |
| 4 | `order-types.aura` | `(api-make-parent id side qty px-limit tif)`, `(api-parent? o)`, `(api-parent-qty o)`, `(api-parent-side o)` |
| 5 | `accounts.aura` | `(api-account-list)`, `(api-account-acct acct)`, `(api-account-share acct)` |
| 6 | `slicer-pov.aura` | `(api-slice-pov parent mkt-volumed children)` |
| 7 | `slicer-twap.aura` | `(api-slice-twap parent horizon-secs slot-secs children)` |
| 8 | `slicer-vwap.aura` | `(api-slice-vwap parent vwap-buckets children)` |
| 9 | `slicer-liqseek.aura` | `(api-slice-liquidity parent venues children urgency)` |
| 10 | `router.aura` | `(api-route children venues)`, `(api-route-one child venue)` |
| 11 | `fill-sim.aura` | `(api-simulate-fills routed mid-px volatility)`, `(api-aggregate-fills fills)` |
| 12 | `risk-monitor.aura` | `(api-completion-pct parent fills)`, `(api-risk-breached? parent fills threshold)` |
| 13 | `allocator-fifo.aura` | `(api-allocate-fifo accounts total-filled)` |
| 14 | `allocator-prorata.aura` | `(api-allocate-pro-rata accounts total-filled)` |
| 15 | `allocator-filledqty.aura` | `(api-allocate-filled-qty accounts per-account-caps total-filled)` |
| 16 | `main.aura` | (scenario driver — see §4; no exports) |

Top-level state is shared across files in one Aura invocation, so `(define *venues* …)` in `venue-registry.aura` is visible in `router.aura` / `fill-sim.aura` / `main.aura`.

---

## 3. API Contracts (per module)

### 3.1 `util.aura`
- `(api-round2 n)` → number rounded to 2 decimals (truncate, no banker's rounding).
- `(api-pad-right s n)` → string left-aligned, right-padded with spaces to width `n` (for aligned printing).
- `(api-now-tick)` → integer monotonic tick from a hidden `(define *tick* 0)` with `(set! *tick* (+ *tick* 1))`.

### 3.2 `market-clock.aura`
- `(api-trading-day?)` → `#t` (toy: always open).
- `(api-slot-count horizon-secs slot-secs)` → `(quotient horizon-secs slot-secs)` integer children for TWAP.

### 3.3 `venue-registry.aura`
Holds `*venues*` as an alist `((NYSE . (fee 0.0003 lat 1)) (ARCA . (fee 0.0002 lat 2)) (IEX . (fee 0.0009 lat 1)) (BATS . (fee 0.0002 lat 2)) (DARK1 . (fee 0.0001 lat 3)))`.
- `(api-venue-list)` → list of venue symbols.
- `(api-venue-fee venue)` → fee as decimal.
- `(api-venue-latency venue)` → latency in ticks.

### 3.4 `order-types.aura`
An order is an alist: `((id . id) (side . BUY|SELL) (qty . n) (px . n) (tif . DAY|GTC))`.
- `(api-make-parent id side qty px-limit tif)` → parent order alist.
- `(api-parent? o)`, `(api-parent-qty o)`, `(api-parent-side o)` → accessors that return `#f` if `o` is not a parent (used to guard children vs. fills).

### 3.5 `accounts.aura`
`api-account-list` returns three accounts built from alists:

- `(api-account-acct a)`, `(api-account-share a)` → accessors.

### 3.6 Slicers (4 files)
All slicers take a parent order + strategy parameters + desired child count, and return a list of child order alists (same shape as parent but with sequential `id` like `C-0001`, fraction-of-parent `qty` summing to parent qty exactly). Strategies:

- **POV** (`slicer-pov.aura`): `(api-slice-pov parent mkt-volumed children)` — sizes each child proportional to that slice's share of `mkt-volumed` (a list of length `children`). If `mkt-volumed` is shorter than `children`, pad with `1`s.
- **TWAP** (`slicer-twap.aura`): `(api-slice-twap parent horizon-secs slot-secs children)` — equal-size children whose count comes from `api-slot-count`. Resamples to match `children` argument.
- **VWAP** (`slicer-vwap.aura`): `(api-slice-vwap parent vwap-buckets children)` — sizes children proportional to `vwap-buckets` (weights summing to 1.0).
- **Liquidity-seeking** (`slicer-liqseek.aura`): `(api-slice-liquidity parent venues children urgency)` — distributes children round-robin across `venues`, sizes scale by `(1 + urgency/10)`.

Each slicer internally rounds to integer shares using `api-round2` and adjusts the last child so `sum(child.qty) = parent.qty` exactly.

### 3.7 `router.aura`
- `(api-route children venues)` → returns list of routed pairs `((child . c) (venue . v))`.
- `(api-route-one child venue)` → single routed pair. Routing strategy: greedy by venue latency ascending, then by fee ascending, picking at most one child per venue per round; remainder overflows to the next venue.

### 3.8 `fill-sim.aura`
- `(api-simulate-fills routed mid-px volatility)` → list of fills. Each fill is an alist `((venue . v) (qty . n) (px . n) (tick . t))`. Fill generation uses a deterministic linear-congruential step seeded from `(api-now-tick)` so output is reproducible across runs but varies with scenario inputs. Partial fills possible.
- `(api-aggregate-fills fills)` → `((total-qty . n) (avg-px . n) (venues-used . (…)) (num-fills . n))`. `avg-px` is volume-weighted, rounded via `api-round2`.

### 3.9 `risk-monitor.aura`
- `(api-completion-pct parent fills)` → `(/ filled-qty parent-qty)` as a number, rounded via `api-round2`.
- `(api-risk-breached? parent fills threshold)` → `#t` if `completion-pct < threshold` *and* at least 50% of slots have elapsed (toy: uses `(api-now-tick)` and elapsed = tick count since parent creation). Default `threshold = 0.80`.

### 3.10 Allocators (3 files)
All return an alist `((AC1 . n) (AC2 . n) (AC3 . n))` whose values sum to `total-filled` exactly (last account absorbs rounding).

- `(api-allocate-fifo accounts total-filled)` — drains accounts in declared order; later accounts only get filled once earlier ones are "saturated" (toy: caps = `share * 2 * total-filled`, so first accounts fill up first).
- `(api-allocate-pro-rata accounts total-filled)` — each account gets `round2(share * total-filled)`; remainder to largest share.
- `(api-allocate-filled-qty accounts per-account-caps total-filled)` — caps are explicit; unused capacity forfeited (`#t` returned as `unused =` list by appending to a side alist key).

---

## 4. Scenario Steps (`main.aura`)

`main.aura` orchestrates the run. It **must call** the module APIs to derive every printed value.



`STRATEGY_CHOSEN` is selectable (the scenario fixes `TWAP`, but the slicer chosen is read from a `define *strategy*` so swapping to `POV`/`VWAP`/`LIQSEEK` is a one-line edit and still produces a valid contract). All 16 keys must print even if some are `0` / `#f`.

---

## 5. Anti-Hardcode

`main.aura` is **rejected** if any of these hold:
- Any `KEY=value` line uses a string literal that isn't produced by an API call (e.g. writing `display "FILLED_CHILD_QTY=8750"` directly).
- `NUM_CHILDREN` is computed with anything other than `(length CH)`.
- `TOTAL_CHILD_QTY` is computed with anything other than `(apply + (map api-parent-qty CH))`.
- `AVG_FILL_PX` is computed with anything other than `(cdr (assq 'avg-px A))`.
- `ALLOC_CHECKSUM` is not the result of comparing `(apply + (map cdr AL))` against the filled qty.
- `STRATEGY_CHOSEN` is hardcoded as the literal `"TWAP"` instead of `*strategy*` symbol → string.

To verify: change `*strategy*` to `'POV` in `main.aura`; the contract still prints and `TOTAL_CHILD_QTY` / `NUM_CHILDREN` / `FILLED_CHILD_QTY` recompute correctly.

---

## 6. How to Run



The CLI loads files in order on a shared top-level; `main.aura` runs the scenario and prints the 16-line contract to stdout.

---

## 7. Notes on Determinism

`fill-sim.aura` uses a seeded LCG `(state := (a*state + c) mod m)` with `a=1103515245`, `c=12345`, `m=2^31`, seeded by `(api-now-tick)`. Because the simulator's first call to `api-now-tick` happens after slicer/router setup (a fixed number of ticks), the fill stream is deterministic **per strategy** but differs **between** `POV`/`TWAP`/`VWAP`/`LIQSEEK` runs — which is what we want for anti-hardcode.
json dogfood
{
  "files": [
    "util.aura",
    "market-clock.aura",
    "venue-registry.aura",
    "order-types.aura",
    "accounts.aura",
    "slicer-pov.aura",
    "slicer-twap.aura",
    "slicer-vwap.aura",
    "slicer-liqseek.aura",
    "router.aura",
    "fill-sim.aura",
    "risk-monitor.aura",
    "allocator-fifo.aura",
    "allocator-prorata.aura",
    "allocator-filledqty.aura",
    "main.aura"
  ],
  "entry": "main.aura",
  "run_mode": "cli_multi",
  "expect_keys": [
    "PARENT_ID",
    "PARENT_SIDE",
    "PARENT_QTY",
    "STRATEGY_CHOSEN",
    "NUM_CHILDREN",
    "TOTAL_CHILD_QTY",
    "FILLED_CHILD_QTY",
    "COMPLETION_PCT",
    "VENUES_USED",
    "AVG_FILL_PX",
    "NUM_FILLS",
    "RISK_BREACHED",
    "ALLOC_RULE",
    "ALLOC_ACCOUNTS",
    "ALLOC_TOTAL_FILLED",
    "ALLOC_CHECKSUM"
  ],
  "source_res": [
    "\\(define\\s+\\(api-round2\\b",
    "\\(define\\s+\\(api-pad-right\\b",
    "\\(define\\s+\\(api-now-tick\\b",
    "\\(define\\s+\\(api-trading-day\\?\\b",
    "\\(define\\s+\\(api-slot-count\\b",
    "\\(define\\s+\\(api-venue-list\\b",
    "\\(define\\s+\\(api-venue-fee\\b",
    "\\(define\\s+\\(api-venue-latency\\b",
    "\\(define\\s+\\(api-make-parent\\b",
    "\\(define\\s+\\(api-parent\\?\\b",
    "\\(define\\s+\\(api-parent-qty\\b",
    "\\(define\\s+\\(api-parent-side\\b",
    "\\(define\\s+\\(api-account-list\\b",
    "\\(define\\s+\\(api-account-acct\\b",
    "\\(define\\s+\\(api-account-share\\b",
    "\\(define\\s+\\(api-slice-pov\\b",
    "\\(define\\s+\\(api-slice-twap\\b",
    "\\(define\\s+\\(api-slice-vwap\\b",
    "\\(define\\s+\\(api-slice-liquidity\\b",
    "\\(define\\s+\\(api-route\\b",
    "\\(define\\s+\\(api-route-one\\b",
    "\\(define\\s+\\(api-simulate-fills\\b",
    "\\(define\\s+\\(api-aggregate-fills\\b",
    "\\(define\\s+\\(api-completion-pct\\b",
    "\\(define\\s+\\(api-risk-breached\\?\\b",
    "\\(define\\s+\\(api-allocate-fifo\\b",
    "\\(define\\s+\\(api-allocate-pro-rata\\b",
    "\\(define\\s+\\(api-allocate-filled-qty\\b"
  ]
}
```
