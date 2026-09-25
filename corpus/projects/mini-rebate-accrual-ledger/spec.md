# GOAL.md — Rebate Accrual Engine with Retroactive True-Ups

A small in-memory rebate accrual engine written in Aura (Lisp-like). It computes
volume, growth, and promotional rebates across a customer hierarchy, applies
tiered thresholds, supports a retroactive lookback window, and posts periodic
true-ups to a payable subledger. Distinguishes **paid-in-advance** (paid before
earned) from **arrears** (paid after earned) semantics, and reserves a
dispute holdback so the payable posted is the net of expected reversals.

The engine is deliberately built on lists/alists only — no structs, no hashes.
State (sales events, accruals, subledger) lives in mutable top-level cells via
`set!`. APIs are pure functions that take state plus arguments.

## 1. Stdout Contract

`main.aura` prints exactly the following 12 `KEY=value` lines, in order. Values
are computed by calling the module APIs, not hardcoded.



## 2. Module Table

Each `.aura` file exposes a small set of `define`d APIs. Files are loaded in
the order listed; the last file is `main.aura`.

| File | Required `define`d APIs |
| --- | --- |
| `lib/util.aura` | `(api make-kv)`, `(api kv-put)`, `(api kv-get)`, `(api kv-keys)`, `(api sum)`, `(api round2)` |
| `lib/hierarchy.aura` | `(api build-hierarchy)`, `(api descendants-of)`, `(api aggregate-attribute)` |
| `lib/tiers.aura` | `(api make-tier-table)`, `(api tier-qualifies?)`, `(api tier-rebate-rate)`, `(api tier-bonus)` |
| `lib/sales.aura` | `(api record-sale)`, `(api events-in-period)`, `(api total-volume)`, `(api growth-vs-prior)` |
| `lib/promotions.aura` | `(api make-promo)`, `(api promo-applies?)`, `(api promo-amount)` |
| `lib/retro.aura` | `(api retro-window)`, `(api retro-qualify?)`, `(api retro-bonus-rate)` |
| `lib/disputes.aura` | `(api open-dispute)`, `(api dispute-holdback)`, `(api release-dispute)` |
| `lib/accruals.aura` | `(api accrue-volume-rebate)`, `(api accrue-growth-rebate)`, `(api accrue-promo-rebate)`, `(api gross-accrued)`, `(api semantic-mode)` |
| `lib/trueups.aura` | `(api trueup-due?)`, `(api post-trueup)`, `(api advance-vs-accrued)` |
| `lib/subledger.aura` | `(api subledger-init)`, `(api subledger-debit)`, `(api subledger-credit)`, `(api subledger-balance)`, `(api subledger-lines)` |
| `seed/seed-customers.aura` | `(api seed-customers)` |
| `seed/seed-programs.aura` | `(api seed-programs)`, `(api seed-tiers)`, `(api seed-promotions)` |
| `seed/seed-events.aura` | `(api seed-sales-events)`, `(api seed-disputes)` |
| `seed/seed-config.aura` | `(api seed-retro-window)`, `(api seed-trueup-cadence)`, `(api seed-semantic-modes)` |
| `main.aura` | `(api main)` |

## 3. Scenario Steps (executed inside `main.aura`)

1. Load util, build an alist-backed KV for state.
2. Call `seed-customers` → list of `(cust-id . parent)` pairs and attribute alists.
3. Call `build-hierarchy` on the customer list.
4. Call `seed-programs` / `seed-tiers` / `seed-promotions` → programs, tier tables, promos.
5. Call `seed-sales-events` → append events to the global event log via `record-sale`.
6. Call `seed-disputes` → register open disputes per customer.
7. Call `seed-retro-window`, `seed-trueup-cadence`, `seed-semantic-modes` for config.
8. For each hierarchy root, aggregate sales events; for each descendant call
   `total-volume`, `growth-vs-prior`, and `events-in-period`.
9. For each (customer, program) pair, call `tier-qualifies?` then
   `accrue-volume-rebate`, `accrue-growth-rebate`, `accrue-promo-rebate`
   (using `promo-applies?` / `promo-amount`).
10. Call `retro-qualify?` for each prior-period event and apply `retro-bonus-rate`.
11. Call `open-dispute` for disputed customers; compute `dispute-holdback`.
12. Initialize `subledger-init`. For each posting, call `subledger-debit` /
    `subledger-credit`; net = `subledger-balance`.
13. For programs where `trueup-due?` returns true, call `post-trueup` and
    `advance-vs-accrued` (paid-in-advance vs arrears reconciliation).
14. Print the 12 `KEY=value` lines in order.

## 4. Anti-Hardcode

`main.aura` MUST:
- Build all state by calling the seed APIs and event APIs.
- Compute every numeric output by traversing the event log / subledger.
- Iterate with `map`/recursion over the customer/program lists — never inline
  literal numbers for gross/net/holdback values.
- Round only at print time via `round2`; intermediate math stays unrounded.

It MUST NOT:
- Embed the expected `GROSS_REBATE_ACCRUED`, `SUBLEDGER_PAYABLE_BALANCE`, etc.
  as literal strings.
- Skip the engine pipeline (e.g., printing without calling accrual APIs).
- Use any data structure outside lists / alists / numbers / strings.

## 5. How to Run



Expected exit: 0. Stdout must contain exactly the 12 `KEY=value` lines above,
in the specified order, with no extra lines.
