# GOAL.md — mini-subscription-proration-ledger

## Overview

A small, in-memory **subscription proration ledger** written in Aura. The system models a SaaS-style billing ledger with double-entry postings (every debit has a matching credit). It supports:

- Plan changes (upgrade / downgrade) with daily proration across the active billing period.
- Mid-cycle signups and cancellations (credits for unused days).
- Manual credits (goodwill, refunds) posted as balanced two-line journal entries.
- A daily proration sweep that posts, for any open subscription, the daily portion of the current period's fee.

Each posting is recorded as a journal line of the shape `(ts acct dr cr memo)`, and balances are computable per account. The system emits a stable stdout contract describing the trial run's final state.

## Exact stdout contract

After loading all 13 files via `aura file1.aura … main.aura`, the program MUST print **exactly** the following 12 `KEY=value` lines, in this order, terminated by a final newline. Values are computed by the program from the API calls (no hard-coding):



`LEDGER_BALANCED=true` iff total debits equal total credits across all journal lines.

## Module table (13 Aura files, loaded in this order)

| # | File | Required exported forms |
|---|------|--------------------------|
| 1 | `money.aura` | `(api money-cents d)`, `(api money-add a b)`, `(api money-sub a b)`, `(api money-mul a n)`, `(api money-div a n)`, `(api money-zero)` |
| 2 | `date.aura` | `(api date-day d)`, `(api date-from-yyyy-mm-dd s)`, `(api date-to-yyyy-mm-dd d)`, `(api date-add-days d n)`, `(api date-diff-days a b)`, `(api date=? a b)`, `(api date<? a b)` |
| 3 | `plan.aura` | `(api make-plan id name monthly-cents)`, `(api plan-id p)`, `(api plan-name p)`, `(api plan-monthly-cents p)`, `(api plan-lookup plans id)` |
| 4 | `account.aura` | `(api make-account code type)`, `(api acct-code a)`, `(api acct-type a)`, `(api account-lookup accounts code)`, `(api coa-default)` |
| 5 | `journal.aura` | `(api make-line ts acct dr cr memo)`, `(api line-acct l)`, `(api line-dr l)`, `(api line-cr l)`, `(api line-memo l)`, `(api journal-append! j l)`, `(api journal-all j)` |
| 6 | `proration.aura` | `(api daily-rate-cents monthly-cents period-days)`, `(api prorate-upgrade old-monthly new-monthly days-remaining period-days)`, `(api prorate-credit monthly-cents unused-days period-days)` |
| 7 | `subscription.aura` | `(api make-sub id plan-id started-on period-days)`, `(api sub-id s)`, `(api sub-plan-id s)`, `(api sub-started-on s)`, `(api sub-days-remaining s on period-days)`, `(api sub-days-used s on)`, `(api sub-change-plan! s new-plan-id on)` |
| 8 | `ledger.aura` | `(api make-ledger)`, `(api ledger-add-line! lg line)`, `(api ledger-lines lg)`, `(api ledger-balance lg account-code)`, `(api ledger-total-debits lg)`, `(api ledger-total-credits lg)`, `(api ledger-balanced? lg)` |
| 9 | `posting.aura` | `(api post-charge! lg accounts ts sub amount-cents memo)`, `(api post-upgrade! lg accounts ts sub old-plan new-plan days-remaining period-days)`, `(api post-credit! lg accounts ts sub amount-cents memo)`, `(api post-daily-accrual! lg accounts ts sub day-idx period-days)` |
| 10 | `scenario.aura` | `(api build-catalog)`, `(api build-accounts)`, `(api scenario-date-anchor)`, `(api run-scenario)` |
| 11 | `report.aura` | `(api report-summarize lg accounts subs)`, `(api report-key-count subs)`, `(api report-line-count lg)`, `(api report-flag-balanced lg)`, `(api report-ar-balance lg accounts)` |
| 12 | `print.aura` | `(api print-row key value)`, `(api print-result summary)` |
| 13 | `main.aura` | (driver — calls APIs and prints the 12 KEY=value lines) |

## Scenario steps (executed inside `run-scenario`, called by `main.aura`)

1. **Build catalog** of two plans via `build-catalog`:
   - `basic` → "Basic" @ 4900 cents/month
   - `pro`   → "Pro"   @ 9900 cents/month
2. **Build chart of accounts** via `build-accounts` (codes):
   - `AR`  (asset)         — Accounts Receivable
   - `REV_A` (revenue)     — Plan A revenue
   - `REV_B` (revenue)     — Plan B revenue
   - `CRED` (liability)    — Customer credits / deferred revenue
3. **Anchor date** = `2025-03-01` (returned by `scenario-date-anchor`).
4. **Create two subscriptions**, both starting at anchor with a 30-day period:
   - `sub-1` on plan `basic`
   - `sub-2` on plan `pro`
5. **Day 1** — initial charges posted via `post-charge!` for each subscription (1/30 of monthly each, AR ↔ Revenue).
6. **Day 10** — `sub-1` upgrades to `pro`. `post-upgrade!` prorates the difference (20 days remaining, 30-day period) and posts the upgrade delta: AR debit, `REV_A` credit, `REV_B` debit.
7. **Day 12** — goodwill credit of 1500 cents issued to `sub-2` via `post-credit!` (AR credit, `CRED` debit).
8. **Days 2..30** — `post-daily-accrual!` is invoked once per remaining day for both subscriptions, posting 1/30 of the **current** plan's monthly fee (after sub-1's upgrade, sub-1 accrues to `REV_B`).
9. Summarize via `report-summarize`, then `main.aura` prints the 12 `KEY=value` rows through `print-row`.

## Anti-hardcode notes

- Every printed value comes from a list traversal / arithmetic over real postings stored in the in-memory ledger.
- `SUB_COUNT` = length of the subscription list built in step 4.
- `JOURNAL_LINES` = `(length (ledger-lines lg))`.
- `TOTAL_DEBITS_CENTS` / `TOTAL_CREDITS_CENTS` = sums computed by `ledger-total-debits` / `ledger-total-credits`.
- `ACCT_*_BALANCE_CENTS` = `(ledger-balance lg "AR")` etc., where balances are net debits minus credits per account, scaled from cents.
- `LEDGER_BALANCED` = result of `ledger-balanced?`.
- Plan monthly cents and period days are looked up from the catalog (built via `make-plan` calls) — not embedded as literals in `main.aura`.
- Changing any plan price or period-days argument in `scenario.aura` would change the output values, proving the main is not just echoing constants.

## How to run

```sh
aura money.aura date.aura plan.aura account.aura journal.aura \
     proration.aura subscription.aura ledger.aura posting.aura \
     scenario.aura report.aura print.aura main.aura
json dogfood
{"files":["money.aura","date.aura","plan.aura","account.aura","journal.aura","proration.aura","subscription.aura","ledger.aura","posting.aura","scenario.aura","report.aura","print.aura","main.aura"],"entry":"main.aura","run_mode":"cli_multi","expect_keys":["SUB_COUNT","PLAN_A_MONTHLY_CENTS","PLAN_B_MONTHLY_CENTS","PERIOD_DAYS","JOURNAL_LINES","TOTAL_DEBITS_CENTS","TOTAL_CREDITS_CENTS","ACCT_AR_BALANCE_CENTS","ACCT_REV_PLAN_A_BALANCE_CENTS","ACCT_REV_PLAN_B_BALANCE_CENTS","ACCT_CREDIT_BALANCE_CENTS","LEDGER_BALANCED"],"source_res":["\\(define\\s+\\(api-money-cents\\b","\\(define\\s+\\(api-date-from-yyyy-mm-dd\\b","\\(define\\s+\\(api-make-plan\\b","\\(define\\s+\\(api-make-account\\b","\\(define\\s+\\(api-make-line\\b","\\(define\\s+\\(api-daily-rate-cents\\b","\\(define\\s+\\(api-make-sub\\b","\\(define\\s+\\(api-make-ledger\\b","\\(define\\s+\\(api-post-charge!\\b","\\(define\\s+\\(api-build-catalog\\b","\\(define\\s+\\(api-report-summarize\\b","\\(define\\s+\\(api-print-row\\b","\\(define\\s+\\(api-run-scenario\\b"]}
```
