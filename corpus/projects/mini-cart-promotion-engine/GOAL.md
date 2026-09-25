# Promotional Pricing Engine

## Overview

A composable promotional pricing engine for an in-memory commerce scenario. The engine evaluates a sequence of promotion rules (percent-off, fixed-amount-off, buy-X-get-Y, threshold discount) against a cart, stacks eligible promotions, respects exclusion sets, and records coupon redemptions in a ledger keyed by coupon code. All state is held in lists and alists (no hash tables, no records). The main scenario loads ~14 `.aura` files, builds a catalog, populates a cart, applies several promotions in a defined order, and emits a stable set of `KEY=value` lines describing the totals and the redemption ledger.

## Exact stdout contract

The program must print exactly these lines, in this order, each terminated by a newline:



Values are computed by the engine (see module table); the contract fixes the *keys* and the *order*. A Python reference harness will later verify each numeric/string value.

## Module table

| File | Required `(define (api …))` exports |
| --- | --- |
| `catalog.aura` | `(api catalog-make)`, `(api catalog-add cat sku name price-cents category)`, `(api catalog-find cat sku)`, `(api catalog-size cat)` |
| `cart.aura` | `(api cart-empty)`, `(api cart-add line cart sku qty)`, `(api cart-lines cart)`, `(api cart-line-count cart)`, `(api cart-subtotal cart catalog)` |
| `promotion.aura` | `(api promotion-make kind code params)`, `(api promotion-code p)`, `(api promotion-kind p)`, `(api promotion-excludes? p other-code)` |
| `registry.aura` | `(api registry-empty)`, `(api registry-add reg promo)`, `(api registry-all reg)`, `(api registry-count reg)` |
| `eligibility.aura` | `(api eligible-promotions cart registry)`, `(api excluded-promotions cart registry eligible)` |
| `stacking.aura` | `(api stack-promotions eligible)`, `(api stacking-order kind)` |
| `evaluator.aura` | `(api eval-percent cart promo)`, `(api eval-fixed cart promo)`, `(api eval-bxgy cart promo)`, `(api eval-threshold cart promo)`, `(api eval-promotion cart promo)` |
| `ledger.aura` | `(api ledger-empty)`, `(api ledger-record ledger code)`, `(api ledger-uses ledger code)`, `(api ledger-total ledger)`, `(api ledger-codes ledger)` |
| `totals.aura` | `(api compute-subtotal cart catalog)`, `(api compute-discount cart stacked)`, `(api compute-final subtotal discount)` |
| `format.aura` | `(api join-pipe xs)`, `(api join-comma xs)`, `(api cents->string n)` |
| `rules/aura_rules_pct.aura` | `(api install-pct10 registry)` |
| `rules/aura_rules_fixed.aura` | `(api install-fixed500 registry)` |
| `rules/aura_rules_bxgy.aura` | `(api install-bxgy1 registry)` |
| `main.aura` | (entry point — calls APIs from every module above and prints the 14 contract keys) |

## Scenario steps (executed in `main.aura`)

1. Build an empty catalog. Add four SKUs across two categories (`book`, `office`).
2. Build an empty cart and add three lines referencing catalog SKUs.
3. Build an empty promotion registry and install four promotions:
   - `PCT10` — 10% off the cart subtotal, category scope `book`.
   - `FIX500` — flat 500 cents off, minimum subtotal 20 000 cents.
   - `BXGY1` — buy 2 get 1 free on category `office` (cheapest free unit priced at catalog price).
   - `THRESH5000` — 5000 cents off once subtotal exceeds 30 000 cents, but marked as excluding `PCT10`.
4. Compute `SUBTOTAL_CENTS` via `(compute-subtotal cart catalog)`.
5. Compute `ELIGIBLE_PROMOTIONS` via `(eligible-promotions cart registry)`.
6. Compute `EXCLUDED_PROMOTIONS` via `(excluded-promotions cart registry eligible)` (returns `THRESH5000` because its exclusion list references `PCT10`, which is in the eligible set).
7. Compute `STACKED_PROMOTIONS` via `(stack-promotions eligible)` — the stacked set drops excluded codes and reorders by stacking priority: percent → fixed → bxgy.
8. For each stacked promotion, evaluate its discount in cents and accumulate into `DISCOUNT_CENTS` via `(compute-discount cart stacked)`.
9. Compute `FINAL_TOTAL_CENTS = SUBTOTAL_CENTS - DISCOUNT_CENTS` via `(compute-final …)`.
10. Record each stacked promotion in the ledger and emit `COUPONS_REDEEMED`, `LEDGER_COUNT`, and per-coupon `LEDGER_<CODE>_USES` counts via `(ledger-uses …)`.
11. Emit `CATALOG_SIZE`, `CART_LINE_COUNT`, `RULE_COUNT` for completeness.
12. Print all 14 keys using `(display k)` `(display "=")` `(display v)` `(newline)`.

## Anti-hardcode

`main.aura` must:

- Call `(catalog-add …)` four times and `(registry-add …)` four times — no static `CATALOG_SIZE=4` literal.
- Call `(cart-add …)` three times — no static `CART_LINE_COUNT=3` literal.
- Call `(compute-subtotal …)`, `(compute-discount …)`, `(compute-final …)` so numeric values are derived, not written as literals.
- Iterate `stacked` with `set!` and `cons` to print codes — no hand-typed `PCT10|FIX500|BXGY1` string literal.
- Iterate the ledger to produce both `COUPONS_REDEEMED` and per-code `LEDGER_*_USES` lines.

If any of the API calls above are removed and replaced with literal strings/numbers, the contract is violated.

## How to run



All files share one top-level Aura invocation. `main.aura` is the entry point and is loaded last.
