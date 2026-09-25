# GOAL.md — Mini Invoice Dunning Collector

## Overview
A multi-file Aura program that runs an invoice dunning (collections) workflow. It loads an AR portfolio, partitions unpaid invoices into aging buckets (current / 1-30 / 31-60 / 61-90 / 90+), walks each invoice through a stage-based cadence (reminder → firm notice → final notice → writeoff review), honors customer promises-to-pay (PTPs) with calendar holds, applies tiered late-payment fees, and emits an audit trail. All state is in-memory lists / alists.

## Stdout Contract (KEY=value, in order)
1. `PORTFOLIO_INVOICES=<int>`
2. `PORTFOLIO_OPEN_BALANCE=<int cents>`
3. `BUCKET_CURRENT=<int>`
4. `BUCKET_1_30=<int>`
5. `BUCKET_31_60=<int>`
6. `BUCKET_61_90=<int>`
7. `BUCKET_90_PLUS=<int>`
8. `REMINDERS_SENT=<int>`
9. `FIRM_NOTICES_SENT=<int>`
10. `FINAL_NOTICES_SENT=<int>`
11. `PROMISES_HONORED=<int>`
12. `PROMISES_BROKEN=<int>`
13. `LATE_FEES_COLLECTED=<int cents>`
14. `WRITEOFFS=<int cents>`
15. `AUDIT_ENTRIES=<int>`
16. `RUN_OK=#t`

## Module Table

| File | Required API forms |
|---|---|
| `data.aura` | `(define seed-portfolio)`, `(define (api-portfolio-data))` |
| `invoice.aura` | `(define (api-invoice-make id cust amount due-day status))`, `(define (api-invoice-id i))`, `(define (api-invoice-customer i))`, `(define (api-invoice-amount i))`, `(define (api-invoice-due-day i))`, `(define (api-invoice-status i))`, `(define (api-invoice-age-days i today))`, `(define (api-invoice-set-status i s))` |
| `aging.aura` | `(define (api-bucket-classify days))`, `(define (api-aging-bucketize invoices today))` |
| `fee.aura` | `(define (api-fee-rate days-past-due))`, `(define (api-fee-applicable? invoice today))`, `(define (api-fee-compute invoice today))` |
| `promise.aura` | `(define (api-promise-make cust invoice-id by-day))`, `(define (api-promise-valid? p today))`, `(define (api-promise-honored? p today))`, `(define (api-promise-add ptps p))`, `(define (api-promise-find ptps invoice-id))` |
| `notice.aura` | `(define (api-notice-stage invoice ptps today))`, `(define (api-notice-template stage invoice))`, `(define (api-notice-send! state stage invoice))`, `(define (api-notice-counters state))` |
| `writeoff.aura` | `(define (api-writeoff-eligible? invoice today))`, `(define (api-writeoff-amount invoice))`, `(define (api-writeoff-record! state invoice))` |
| `audit.aura` | `(define (api-audit-log! state msg))`, `(define (api-audit-entries state))`, `(define (api-audit-format e))` |
| `state.aura` | `(define (api-state-make))`, `(define (api-state-get state key))`, `(define (api-state-set! state key val))`, `(define (api-state-add! state key val))` |
| `runner.aura` | `(define (api-run-dunning portfolio ptps today))` |
| `report.aura` | `(define (api-report-summary state buckets))` |
| `main.aura` | (entrypoint — orchestrates and prints KEY=… lines) |

## Scenario Steps (main.aura)
1. Call `api-portfolio-data` to obtain a seeded list of invoices (mix of statuses: open, paid, disputed) plus a "today" day counter.
2. Call `api-aging-bucketize` over the open invoices to obtain a 5-bucket alist `(current . n) (1-30 . n) …`.
3. For each invoice, walk stages: call `api-notice-stage` (returns `'reminder | 'firm | 'final | 'none`), then `api-notice-send!` to bump counters and `api-audit-log!`.
4. For each stage that is `'firm` or `'final`, call `api-fee-applicable?` then `api-fee-compute`; accumulate cents into `LATE_FEES_COLLECTED` and `api-audit-log!` "LATE_FEE".
5. Seed a small list of promises-to-pay and pass it through every iteration: `api-promise-valid?` + `api-promise-honored?`. Increment `PROMISES_HONORED` / `PROMISES_BROKEN` and write `api-audit-log!`.
6. For invoices where stage = `'final` and age > 90 days, call `api-writeoff-eligible?` then `api-writeoff-record!`; sum into `WRITEOFFS` and `api-audit-log!` "WRITEOFF".
7. Call `api-report-summary` to finalize counters, then `display` each KEY=value line in the exact order above, finishing with `RUN_OK=#t`.
8. `api-run-dunning` is exposed for reuse and is called at least once by main.

## Anti-Hardcode
`main.aura` MUST compute values through module APIs — `api-aging-bucketize`, `api-notice-counters`, `api-fee-compute`, `api-promise-honored?`, `api-writeoff-record!`, `api-audit-entries`. Hardcoding literal integers and printing them (e.g. `(display "BUCKET_1_30=4")`) without invoking the API chain is a failure. Each numeric counter must originate from a list traversal that calls at least one `api-*` function per invoice / promise.

## How to Run
