# Variation Margin Call Workflow with Dispute Windows

## Overview

A toy variation margin (VM) call engine for derivative portfolios. The system:

1. Holds **counterparties** each governed by a **CSA (Credit Support Annex)** — agreement parameters include `threshold`, `mta` (Minimum Transfer Amount), `rounding`, `currency`, `dispute_window_hours`, and `interest_rate_bps` applied to unpaid VM.
2. Holds **trades** per counterparty with notional, direction, and current market value.
3. Computes daily **mark-to-market (MtM) net value** per counterparty.
4. Issues **margin calls** when exposure exceeds `threshold + mta` (and rounds to agreed `rounding`).
5. Runs a **dispute timer**: any unresolved call past `dispute_window_hours` is auto-confirmed.
6. Accepts **partial settlements** (deliveries) and reduces the outstanding call.
7. Accrues **interest on unpaid margin** at the CSA rate, daily, until settled.
8. Reports portfolio totals, top exposures, and dispute/aging status.

All state lives in-memory in Aura lists/alists. No filesystem I/O.

## Stdout Contract

The scenario (`main.aura`) prints exactly these `KEY=value` lines, in this order:



Numeric values are integers; counterparty ID strings are emitted as the raw id (no quotes).

## Module Table

| File | Required API forms |
|---|---|
| `types.aura` | `(define (make-csa id threshold mta rounding ccy dispute-hours rate-bps))`, `(define (csa-id c))`, `(define (csa-threshold c))`, `(define (csa-mta c))`, `(define (csa-rounding c))`, `(define (csa-ccy c))`, `(define (csa-dispute-hours c))`, `(define (csa-rate-bps c))`, `(define (make-trade cp-id notional direction mv))`, `(define (trade-cp t))`, `(define (trade-notional t))`, `(define (trade-dir t))`, `(define (trade-mv t))`, `(define (make-call id cp-id amount issued-at status))`, `(define (call-id c))`, `(define (call-cp c))`, `(define (call-amount c))`, `(define (call-status s)` returns `'open`/`'disputed`/`'settled`/`'expired`) |
| `portfolio.aura` | `(define (api-portfolio-add-cp cp))`, `(define (api-portfolio-add-trade t))`, `(define (api-portfolio-mtm cp-id))`, `(define (api-portfolio-total-mtm))`, `(define (api-portfolio-counterparties))`, `(define (api-portfolio-trade-count))`, `(define (api-portfolio-trades-for cp-id))` |
| `rounding.aura` | `(define (api-round-up amount rounding))`, `(define (api-round-nearest amount rounding))` |
| `threshold.aura` | `(define (api-call-required? mtm threshold mta))` — `#t` when `mtm >= threshold + mta`; `(define (api-call-amount mtm threshold mta rounding))` |
| `dispute.aura` | `(define (api-open-dispute call-id))`, `(define (api-dispute-count))`, `(define (api-expired-disputes now-hours))` — auto-confirms and returns count of calls whose dispute window elapsed since issuance; `(define (api-call-status call-id))` |
| `settlement.aura` | `(define (api-deliver call-id amount))`, `(define (api-mark-settled call-id))`, `(define (api-call-outstanding call-id))`, `(define (api-total-delivered))`, `(define (api-total-outstanding))`, `(define (api-settled-calls))`, `(define (api-open-calls))` |
| `interest.aura` | `(define (api-accrue-on-call call-id days))`, `(define (api-total-interest))` — interest = `outstanding * rate-bps * days / 10000` (integer, rounded down); `(define (api-interest-for-call call-id))` |
| `reporting.aura` | `(define (api-top-exposure))` — returns `(cp-id . mtm)` of the highest-MtM counterparty, or `'()` if none; `(define (api-summary))` — returns an alist `((mtm . n) (calls . n) (outstanding . n) (interest . n))` |
| `state.aura` | global lists (private): `*csas*`, `*trades*`, `*calls*`, `*deliveries*`, `*interest-ledger*`, `*call-counter*`. Plus `(define (api-reset))`, `(define (api-next-call-id))` |
| `main.aura` | scenario driver — see below |

## Scenario Steps (`main.aura`)

`main.aura` performs:

1. `(api-reset)` from `state.aura`.
2. Build 3 counterparties via `portfolio-add-cp` + `make-csa`:
   - CP-A: threshold 1,000,000, MTA 100,000, rounding 50,000, USD, dispute 24h, 50 bps.
   - CP-B: threshold 500,000, MTA 50,000, rounding 10,000, EUR, dispute 48h, 75 bps.
   - CP-C: threshold 0, MTA 0, rounding 1,000, GBP, dispute 12h, 100 bps.
3. Add ~6 trades across them via `portfolio-add-trade` (mixed long/short, varied MtM).
4. For each CP, ask `portfolio-mtm`, decide a call via `threshold.call-required?` + `threshold.call-amount`, and if required, open one via `dispute` + `state.next-call-id`.
5. Open disputes on 2 of the issued calls (`dispute.open-dispute`).
6. Settle one call fully (`settlement.mark-settled`), one partially (`settlement.deliver` half).
7. Advance clock: call `dispute.expired-disputes` for the 48h window (elapses 1 disputed call), then `interest.accrue-on-call` 3 days on the still-open partially-settled call.
8. Compute final aggregates (`portfolio-total-mtm`, `settlement.total-delivered`, `settlement.total-outstanding`, `dispute.dispute-count`, `interest.total-interest`, `reporting.top-exposure`).
9. Print the 16 `KEY=value` lines in the exact order above.

## Anti-Hardcode

- `main.aura` never prints a literal expected value. Every printed line is derived from a module API call (`portfolio-total-mtm`, `settlement-total-delivered`, etc.).
- Numeric decisions (whether to call, dispute, settle, expire) are driven by the portfolio/trade/CSA inputs the scenario itself seeds, not by hardcoded call lists.
- If you swap any CSA parameter or trade MtM, the `KEY=value` outputs must change accordingly.
- Cross-module flow is real: `threshold.call-required?` consults `portfolio-mtm`; `dispute.expired-disputes` mutates call status which `settlement.total-outstanding` then reflects; `interest.accrue-on-call` reads CSA rate from `types.csa-rate-bps`.

## How to Run



All files share a single top-level; order matters only because `state.aura` and `types.aura` must precede modules that use them. The CLI prints the 16 `KEY=value` lines to stdout.
