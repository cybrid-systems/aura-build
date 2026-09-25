# Tax Calculation Engine — mini-tax-rules-engine

## Overview

A compact in-memory tax-rules engine that loads a hierarchical jurisdiction graph
(Country → State → City → District), resolves which rules apply to a given invoice,
applies exemptions and overrides, and computes per-line tax plus invoice totals.
Demonstrates rule-graph traversal, override precedence, and pure-functional
arithmetic using only lists, alists, and `set!`.

## Exact stdout contract

The scenario must print exactly these `KEY=value` lines, in order, one per line:



(Values are illustrative; the engine must *compute* them via module APIs.
Do not hardcode. Money is shown to 2 decimal places.)

## Module table

| File | Required exported APIs |
|------|-----------------------|
| `rates.aura` | `(make-rate code rate)`, `(rate-code r)`, `(rate-value r)`, `(add-rate alist r)` |
| `jurisdiction.aura` | `(make-jurisdiction code rate children)`, `(jur-code j)`, `(jur-rate j)`, `(jur-children j)`, `(jur-lookup graph code)`, `(jur-path graph code)` |
| `override.aura` | `(make-override target-code field value priority)`, `(ov-target o)`, `(ov-field o)`, `(ov-value o)`, `(ov-priority o)`, `(apply-overrides rules overrides)` |
| `exemption.aura` | `(make-exemption code kind amount predicates)`, `(ex-code e)`, `(ex-kind e)`, `(ex-amount e)`, `(ex-matches? e line)`, `(apply-exemptions line taxable exemptions)` |
| `rules.aura` | `(make-rule jur-code rate)`, `(rule-jur r)`, `(rule-rate r)`, `(merge-rules a b)` |
| `resolver.aura` | `(resolve-rate graph code overrides)`, `(applicable-rate graph target-code overrides)` |
| `line.aura` | `(make-line id qty unit-price category exempt?)`, `(line-amount l)`, `(line-tax l rate taxable)`, `(line-display l tax)` |
| `invoice.aura` | `(make-invoice lines jur-code)`, `(inv-lines inv)`, `(inv-jur inv)`, `(add-line inv ln)` |
| `compute.aura` | `(compute-line-tax line rate exemptions)`, `(compute-invoice invoice graph overrides exemptions)` |
| `format.aura` | `(fmt-money n)` |
| `sample.aura` | `(sample-graph)`, `(sample-overrides)`, `(sample-exemptions)`, `(sample-invoice)` |
| `main.aura` | scenario driver; only file that prints |

All money is stored as exact numbers (cents internally); the formatter rounds to 2dp.

## Scenario steps (in `main.aura`)

1. Load `sample-graph` → alist of jurisdictions (US → CA → SF, US → NY → NYC).
2. Load `sample-overrides` → list of override objects (e.g. SF overrides CITY_RATE).
3. Load `sample-exemptions` → list of exemption objects (e.g. FOOD exempt, BOOKS half).
4. Load `sample-invoice` → invoice with 4 lines addressed to SF.
5. `(resolve-rate graph "SF" overrides)` → traverse US → CA → SF, collect rates,
   then `apply-overrides` to get effective rate (base 0.05 + 0.075 + 0.01 = 0.135).
6. For each line, `(compute-line-tax line effective-rate exemptions)` produces
   `(line-amount l) * effective-rate - exemption`.
7. Sum per-line tax, sum subtotal, print grand total.
8. Print all 16 `KEY=value` lines in the exact order shown above.

## Anti-hardcode

`main.aura` must:
- Call `(sample-graph)`, `(sample-overrides)`, `(sample-exemptions)`, `(sample-invoice)`.
- Call `(resolve-rate …)`, `(compute-line-tax …)`, `(compute-invoice …)`, `(fmt-money …)`.
- Build the displayed values from these API results using `number->string` / `string-append`.
- Not contain any literal that *is* the final value (e.g. no literal `"0.135"` or `"136.20"`
  outside the sample/constant files that feed the engine).

## How to run

```sh
aura rates.aura jurisdiction.aura override.aura exemption.aura rules.aura \
     resolver.aura line.aura invoice.aura compute.aura format.aura \
     sample.aura main.aura
json dogfood
{"files":["rates.aura","jurisdiction.aura","override.aura","exemption.aura","rules.aura","resolver.aura","line.aura","invoice.aura","compute.aura","format.aura","sample.aura","main.aura"],"entry":"main.aura","run_mode":"cli_multi","expect_keys":["COUNTRY_CODE","COUNTRY_RATE","STATE_CODE","STATE_RATE","CITY_CODE","CITY_RATE","EFFECTIVE_RATE","EXEMPTIONS_APPLIED","LINE_COUNT","SUBTOTAL","TAX_TOTAL","GRAND_TOTAL","LINE_0_TAX","LINE_1_TAX","LINE_2_TAX","LINE_3_TAX"],"source_res":["\\(make-rate\\b","\\(make-jurisdiction\\b","\\(make-override\\b","\\(make-exemption\\b","\\(make-rule\\b","\\(resolve-rate\\b","\\(make-line\\b","\\(make-invoice\\b","\\(compute-line-tax\\b","\\(compute-invoice\\b","\\(fmt-money\\b","\\(sample-graph\\b","\\(sample-invoice\\b"]}
```
