# GOAL.md — Credit Limit Hold and Authorization Engine

## 1. Overview
A miniature in-memory **credit-limit hold / authorization engine** for a toy commerce platform. The engine tracks each customer's credit line, open-to-buy exposure from orders, shipments, returns and unposted invoices, decides whether to place a **soft hold** or a **hard hold** on a new order, supports a **manager-override workflow**, and **releases holds incrementally** as payments are posted or shipments reduce exposure. It also computes a per-customer **risk score** from a small pay-history (on-time / late / default buckets). All state lives in lists / alists; no external resources.

Aura is loaded as a multi-file project. `main.aura` calls only the documented module APIs and prints a fixed ordered stdout contract of 12 `KEY=value` lines.

---

## 2. Exact stdout contract

The scenario MUST print exactly these 12 lines, in this order, with the `=` literal separating key and value. Numbers print via `display` (no extra whitespace). Booleans print `#t`/`#f`. Strings are unquoted.



Meaning of each key (used only by the grader — main must compute, not hard-code):

| Key | Meaning |
|-----|---------|
| `CUSTOMERS` | number of distinct customers in the registry |
| `LINE_TOTAL` | sum of every customer's `credit-line` |
| `OTB_AVG` | integer average open-to-buy across customers, rounded down |
| `HARD_HOLDS` | count of currently-active holds of type `hard` |
| `SOFT_HOLDS` | count of currently-active holds of type `soft` |
| `RELEASED` | count of holds released during the scenario (cumulative counter) |
| `PAY_POSTED` | sum of payment amounts applied to customer balances in the scenario |
| `RISK_HIGH` | customers whose risk band is `high` |
| `RISK_MED`  | customers whose risk band is `med`  |
| `RISK_LOW`  | customers whose risk band is `low`  |
| `OVERRIDE_APPROVED` | manager overrides that ended with status `approved` |
| `OVERRIDE_DENIED`   | manager overrides that ended with status `denied`   |

---

## 3. Module table

Each file is a real Aura source file loaded in order on a single Aura CLI invocation. Only listed `define`s are required per file; helpers used internally are allowed.

| # | File | Required `(define (api …))` forms |
|---|------|------------------------------------|
| 1 | `types.aura` | `make-customer`, `customer?`, `customer-id`, `customer-name`, `customer-line`, `customer-balance`, `customer-set-balance!`, `customer-risk` |
| 2 | `risk.aura` | `make-pay-history`, `pay-on-time?`, `pay-late?`, `pay-default?`, `risk-score`, `risk-band` |
| 3 | `exposure.aura` | `exposure-orders`, `exposure-shipments`, `exposure-returns`, `exposure-unposted`, `open-to-buy` |
| 4 | `holds.aura` | `make-hold`, `hold?`, `hold-id`, `hold-cust`, `hold-type`, `hold-amount`, `hold-status`, `hold-set-status!`, `hold-released-amount`, `place-hold!`, `release-hold!`, `active-holds`, `active-hold-for?` |
| 5 | `policy.aura` | `policy-decide`, `policy-soft-threshold`, `policy-hard-threshold` |
| 6 | `override.aura` | `request-override!`, `approve-override!`, `deny-override!`, `override-record`, `override-status` |
| 7 | `payments.aura` | `post-payment!`, `payment-apply-to-holds!` |
| 8 | `shipments.aura` | `record-shipment!`, `shipment-reduces-exposure!` |
| 9 | `returns.aura` | `record-return!`, `return-reduces-exposure!` |
| 10 | `invoices.aura` | `add-unposted-invoice!`, `invoice-amount` |
| 11 | `risk_registry.aura` | `register-customer!`, `all-customers`, `find-customer` |
| 12 | `events.aura` | `event-log`, `log-event!`, `recent-events` |
| 13 | `stats.aura` | `count-customers`, `sum-lines`, `avg-otb`, `count-active-by-type`, `total-released`, `total-pay-posted`, `count-by-risk-band`, `count-overrides-by-status` |
| 14 | `seed.aura` | `seed-scenario!` (populates registry + history + invoices) |
| 15 | `main.aura` | (entry point; no exports required — only uses module APIs) |

---

## 4. Scenario steps (executed in `main.aura`)

`main.aura` is the ONLY file that calls `display` / `newline`. It performs the scenario strictly via module APIs:

1. `(seed-scenario!)` — registers 4 customers with lines `3000, 2500, 2000, 2000` (= `LINE_TOTAL=9500`), seeds pay-history and 2 unposted invoices.
2. **Order A** for cust `c1` amount `2700` → `(policy-decide c1 2700)` → `hard` hold placed. `place-hold!` records it.
3. **Order B** for cust `c2` amount `1200` (within soft threshold) → `soft` hold placed.
4. **Order C** for cust `c2` amount `900` (pushes over soft threshold) → another `soft` hold placed.
5. `request-override!` on Order A's hold for `c1` by a manager.
   - `approve-override!` once → status `approved`.
   - `deny-override!` once (on Order C's hold for `c2`) → status `denied`.
6. `post-payment!` of `300` for `c1`, then `200` for `c2` → `payment-apply-to-holds!` releases 2 holds (Order A's hold fully released by override+payment, Order C's hold released by payment).
7. `record-shipment!` for an `c3` order amount `500` → exposure reduced; no extra release.
8. `record-return!` for `c1` amount `150` → exposure reduced.
9. Compute stats: `count-customers`, `sum-lines`, `avg-otb`, `count-active-by-type`, `total-released`, `total-pay-posted`, `count-by-risk-band`, `count-overrides-by-status`.
10. Print the 12 `KEY=value` lines in the exact order above.

Expected after step 9 (computed by the grader, not hard-coded in main): 4 customers, line total 9500, OTB avg 1837 (floor), 1 hard hold still active (Order B was released, Order C was released → only Order A's hold was released; actually the scenario yields exactly 1 hard + 2 soft originally placed, then 2 released → HARD=1, SOFT=2, RELEASED=2), pay posted 450 (300+200), risk bands yield 1 high, 2 med, 1 low, overrides 1 approved + 1 denied.

---

## 5. Anti-hardcode

- `main.aura` MUST compute every value by calling the module APIs listed in §3. It must not contain literal strings like `"9500"`, `"1837"`, `"1"`, `"2"`, etc. as the displayed values.
- The numbers come from `stats.aura` helpers which themselves iterate over the live registry / holds / events built up through `seed-scenario!`, `place-hold!`, `post-payment!`, `record-shipment!`, `record-return!`, `approve-override!`, `deny-override!`.
- An audit pass must verify: grepping `main.aura` for any of `9500|1837|450|3000|2500|2000` returns **zero** matches as a `display` argument (literals may appear only inside API calls like `seed-scenario!` if needed, but main's printed side must be derived).
- Each module file MUST be loaded and contribute at least one `(define (api-name …))` form (see JSON `source_res`).

---

## 6. How to run



Expected stdout (line order matters, exact strings):



---
