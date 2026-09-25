# GOAL.md — Mini Clearing and Netting Engine

## Overview

A 16-file Aura (Lisp-like) project that simulates a **multilateral clearing and netting engine** for trade counterparties. The engine ingests bilateral trades, applies pay-through hierarchies (CCP → clearing member → client), honors **novation** semantics (replacing gross bilateral exposures with net positions through a central counterparty), respects **minimum-transfer amounts (MTAs)**, and emits **net settlement instructions** for a chosen value date alongside a regulator-style netting efficiency report (gross → net reduction ratios, per-counterparty obligations, cleared/not-cleared splits).

The implementation is purely in-memory: trades are stored as alists, netting walks an adjacency of bilateral exposures, and reporting reduces over the same lists. No external state, no I/O beyond `display`/`newline`.

---

## Exact stdout contract (KEY=value lines, in order)

The program prints exactly these 15 keys, in this exact order. Values are computed at runtime from module APIs — not hardcoded strings.



`COMPLIANCE_CHECK` is `PASS` iff every computed metric is internally consistent (e.g. `NET_OBLIGATIONS ≤ GROSS_OBLIGATIONS`, settlement instruction sum equals net obligations zero-sum, `NETTING_EFFICIENCY = round(1 - NET/GROSS, 4)`).

---

## Module table

All files are `.aura`. They are loaded sequentially on one Aura CLI invocation, sharing the top-level environment. `main.aura` is last and is the entry point — it calls APIs and prints.

| # | File | Required exported `(define (api …) …)` forms |
|---|------|----------------------------------------------|
| 1 | `types.aura` | `(make-trade id ccy payer payee amount value-date)`, `(trade-id t)`, `(trade-amount t)`, `(trade-payer t)`, `(trade-payee t)`, `(trade-ccy t)`, `(trade-value-date t)`, `(trade? x)` |
| 2 | `registry.aura` | `(register-trade t)`, `(all-trades)`, `(trades-for-date vd)`, `(party-list)`, `(reset-registry!)` |
| 3 | `mta.aura` | `(set-mta! ccy amount)`, `(get-mta ccy)`, `(below-mta? amount ccy)` |
| 4 | `bilateral.aura` | `(gross-exposure vd ccy)`, `(exposure-between a b vd ccy)`, `(all-bilateral-pairs vd ccy)` |
| 5 | `novation.aura` | `(set-novation-policy! mode)` (mode = `'off` or `'ccp`), `(novation-policy)`, `(apply-novation! vd ccy)` |
| 6 | `paythrough.aura` | `(set-paythrough! hierarchy-alist)`, `(paythrough-chain party)`, `(effective-counterparty party)`, `(tier-depth)` |
| 7 | `netting.aura` | `(net-obligations vd ccy)`, `(net-position party vd ccy)`, `(zero-sum? net-map)`, `(settlement-instructions vd ccy)` |
| 8 | `mts.aura` | `(apply-mta-filter vd ccy)`, `(mta-filtered-pairs vd ccy)` |
| 9 | `settlement.aura` | `(build-instructions vd ccy)`, `(instruction-payer i)`, `(instruction-payee i)`, `(instruction-amount i)`, `(instructions-total-out i)` |
| 10 | `efficiency.aura` | `(efficiency-ratio gross net)`, `(largest-single-payment instructions)`, `(cleared-count)`, `(uncleared-count)` |
| 11 | `report.aura` | `(regulator-report vd ccy)`, `(report-lines vd ccy)`, `(report-bic)` |
| 12 | `compliance.aura` | `(check-consistency vd ccy)`, `(zero-sum-ok? vd ccy)`, `(efficiency-bounds-ok? vd ccy)`, `(mtas-applied-ok? vd ccy)` |
| 13 | `calendar.aura` | `(parse-date s)`, `(format-date d)`, `(choose-value-date trades today)`, `(value-date? x)` |
| 14 | `currency.aura` | `(normalize-ccy ccy)`, `(same-ccy? a b)`, `(amount+ a b)`, `(amount- a b)`, `(sum-amounts lst)` |
| 15 | `scenario.aura` | `(seed-scenario!)`, `(party-hierarchy)`, `(scenario-trades)`, `(scenario-ccy)`, `(scenario-value-date)` |
| 16 | `main.aura` | `(run)` — entry, calls scenario + APIs, prints all 15 KEY=value lines |

---

## Scenario steps (executed by `main.aura`)

1. `(seed-scenario!)` → registers a deterministic in-memory trade book across ≥ 5 counterparties and ≥ 2 CCP tiers, single currency.
2. `(set-mta! ccy 1000)` then `(set-paythrough! party-hierarchy)` then `(set-novation-policy! 'ccp)`.
3. `(choose-value-date (all-trades) today)` picks the value date used by all subsequent computations.
4. `(apply-novation! vd ccy)` rewrites bilateral exposures into CCP-mediated positions when policy is `'ccp`.
5. `(apply-mta-filter vd ccy)` discards sub-threshold net legs and records the filtered count.
6. `(net-obligations vd ccy)` produces the netted obligation map; `(zero-sum? net-map)` is asserted true.
7. `(settlement-instructions vd ccy)` and `(build-instructions vd ccy)` produce the final instruction list.
8. `(regulator-report vd ccy)` aggregates gross/net/efficiency figures.
9. `(check-consistency vd ccy)` returns `'PASS` or `'FAIL` and is printed as `COMPLIANCE_CHECK`.
10. `main.aura` prints all 15 KEY=value lines using **only** values returned from the module APIs above — no string literals for numeric content.

---

## Anti-hardcode

`main.aura` must not display the expected metric strings as literals. Every numeric value (trade counts, gross/net obligations, efficiency %, MTA filtered count, instruction count, largest single payment, novation flag, tier depth) must be obtained by calling the corresponding API in the module table, then converted via `number->string`. Only the `KEY=` prefixes, the date format, and the `PASS`/`FAIL` token (the latter from `compliance`) are emitted as literals. The currency code in `REPORT_BIC` may be a literal label from `scenario-ccy`.

---

## How to run

```sh
aura types.aura registry.aura mta.aura bilateral.aura novation.aura paythrough.aura \
     netting.aura mts.aura settlement.aura efficiency.aura report.aura \
     compliance.aura calendar.aura currency.aura scenario.aura main.aura
json dogfood
{
  "files": [
    "types.aura",
    "registry.aura",
    "mta.aura",
    "bilateral.aura",
    "novation.aura",
    "paythrough.aura",
    "netting.aura",
    "mts.aura",
    "settlement.aura",
    "efficiency.aura",
    "report.aura",
    "compliance.aura",
    "calendar.aura",
    "currency.aura",
    "scenario.aura",
    "main.aura"
  ],
  "entry": "main.aura",
  "run_mode": "cli_multi",
  "expect_keys": [
    "VALUE_DATE",
    "TRADE_COUNT",
    "GROSS_OBLIGATIONS",
    "NET_OBLIGATIONS",
    "NETTING_EFFICIENCY",
    "COUNTERPARTY_COUNT",
    "CLEARED_COUNT",
    "UNCLEARED_COUNT",
    "MTA_FILTERED_COUNT",
    "SETTLEMENT_INSTRUCTION_COUNT",
    "LARGEST_SINGLE_NET_PAYMENT",
    "NOVATION_APPLIED",
    "PAY_THROUGH_TIER_DEPTH",
    "REPORT_BIC",
    "COMPLIANCE_CHECK"
  ],
  "source_res": [
    "\\(define\\s+\\(make-trade\\b",
    "\\(define\\s+\\(trade-id\\b",
    "\\(define\\s+\\(trade-amount\\b",
    "\\(define\\s+\\(register-trade\\b",
    "\\(define\\s+\\(all-trades\\b",
    "\\(define\\s+\\(trades-for-date\\b",
    "\\(define\\s+\\(set-mta!\\b",
    "\\(define\\s+\\(below-mta\\?\\b",
    "\\(define\\s+\\(gross-exposure\\b",
    "\\(define\\s+\\(exposure-between\\b",
    "\\(define\\s+\\(apply-novation!\\b",
    "\\(define\\s+\\(set-paythrough!\\b",
    "\\(define\\s+\\(paythrough-chain\\b",
    "\\(define\\s+\\(effective-counterparty\\b",
    "\\(define\\s+\\(net-obligations\\b",
    "\\(define\\s+\\(net-position\\b",
    "\\(define\\s+\\(settlement-instructions\\b",
    "\\(define\\s+\\(apply-mta-filter\\b",
    "\\(define\\s+\\(build-instructions\\b",
    "\\(define\\s+\\(instruction-amount\\b",
    "\\(define\\s+\\(efficiency-ratio\\b",
    "\\(define\\s+\\(largest-single-payment\\b",
    "\\(define\\s+\\(regulator-report\\b",
    "\\(define\\s+\\(check-consistency\\b",
    "\\(define\\s+\\(parse-date\\b",
    "\\(define\\s+\\(choose-value-date\\b",
    "\\(define\\s+\\(normalize-ccy\\b",
    "\\(define\\s+\\(sum-amounts\\b",
    "\\(define\\s+\\(seed-scenario!\\b",
    "\\(define\\s+\\(scenario-ccy\\b",
    "\\(define\\s+\\(scenario-value-date\\b",
    "\\(define\\s+\\(run\\b"
  ]
}
```
