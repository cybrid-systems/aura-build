# Checkout Pipeline Orchestrator

A multi-stage checkout state machine implemented in Aura. The orchestrator validates a shopping cart, computes pricing, runs payment authorization, runs a fraud-scoring hook, and either commits the order or compensates already-completed stages (saga-style rollback). The final program prints a fixed-key stdout contract that an external reference can diff.

## 1. Stdout contract (exact order)

The program must print **exactly** these KEY=value lines, in this order, terminated by a newline after each line:



`OUTCOME` is either `COMMITTED` or `COMPENSATED`. `ROLLBACK_STAGES` is either `NONE` or a comma-separated list of stage names. The reference values for items, totals, auth id, fraud score, and decision are computed by the modules — main.aura does not bake them in.

## 2. Module table

All files are `.aura`. They are loaded on one Aura CLI invocation in the listed order. The last file is the entry point that prints the contract.

| # | File | Required exported API |
|---|------|------------------------|
| 1 | `pipeline/contract.aura` | `(api-version)`, `(api-stage-names)` |
| 2 | `pipeline/state.aura` | `(api-make-state order-id)`, `(api-state-set! st k v)`, `(api-state-get st k)`, `(api-state-mark-done! st stage)`, `(api-state-done? st stage)`, `(api-state-push-rollback! st stage)`, `(api-state-rollback-stages st)` |
| 3 | `pipeline/registry.aura` | `(api-register-stage! name run-fn compensate-fn)`, `(api-lookup-run name)`, `(api-lookup-compensate name)` |
| 4 | `cart/validate.aura` | `(api-validate-cart cart)` |
| 5 | `pricing/compute.aura` | `(api-price-order cart)` — returns `(subtotal-cents tax-cents total-cents)` |
| 6 | `pricing/tax.aura` | `(api-tax-cents subtotal-cents region)` |
| 7 | `payment/authorize.aura` | `(api-authorize-payment state amount-cents)` |
| 8 | `payment/capture.aura` | `(api-capture-payment auth-id)` |
| 9 | `payment/void.aura` | `(api-void-payment auth-id)` |
| 10 | `fraud/score.aura` | `(api-score-fraud state cart amount-cents)` |
| 11 | `fraud/decision.aura` | `(api-fraud-decision score)`, `(api-fraud-threshold)` |
| 12 | `orders/commit.aura` | `(api-commit-order state)` |
| 13 | `orders/cancel.aura` | `(api-cancel-order state)` |
| 14 | `saga/compensate.aura` | `(api-compensate state)` |
| 15 | `saga/orchestrator.aura` | `(api-run-pipeline state cart region)`, `(api-outcome state)`, `(api-order-id state)` |
| 16 | `samples/cart.aura` | `(api-sample-cart)` |
| 17 | `samples/region.aura` | `(api-sample-region)` |
| 18 | `main.aura` | `(api-run)` — entry point, prints the stdout contract |

Total: 18 `.aura` files. Each `api-*` symbol must be a top-level `define` produced by one of the modules above.

## 3. Scenario steps (executed in `main.aura`)

`main.aura` performs these steps, each calling an exported API:

1. `(define VERSION (api-version))`
2. `(define STAGE-NAMES (api-stage-names))`
3. `(define CART (api-sample-cart))`
4. `(define REGION (api-sample-region))`
5. `(define VALID (api-validate-cart CART))` — if invalid, main prints `OUTCOME=REJECTED` and exits.
6. `(define PRICED (api-price-order CART))` — extract `subtotal-cents`, `tax-cents`, `total-cents` via `car`/`cadr`/`caddr`.
7. `(define STATE (api-make-state (api-next-order-id)))`
8. `(api-state-set! STATE 'subtotal (car PRICED))` etc.
9. `(api-authorize-payment STATE (caddr PRICED))` — stores `payment-auth-id` on state.
10. `(api-score-fraud STATE CART (caddr PRICED))` — stores `fraud-score` on state.
11. `(define DECISION (api-fraud-decision (api-state-get STATE 'fraud-score)))`
12. If `DECISION` is `ACCEPT`: call `api-commit-order STATE`, set `OUTCOME=COMMITTED`, rollback stages stays empty.
13. If `DECISION` is `REJECT`: call `api-compensate STATE`, which iterates `api-state-rollback-stages` and calls each stage's compensate fn (e.g. `api-void-payment`), then `api-cancel-order STATE`; set `OUTCOME=COMPENSATED` and populate `ROLLBACK_STAGES` from the state.
14. `(api-run)` prints the 13 KEY=value lines in the exact order above.

`api-fraud-threshold` returns a number (e.g. `60`). The reference fraud-score is derived from the sample cart contents, so main must not hardcode it.

## 4. Anti-hardcode

`main.aura` is forbidden from:
- printing any of the literal expected values (`AUTH-9F2C1E`, `12`, `ACCEPT`, `4298`, etc.) as bare strings,
- skipping the pipeline (e.g. directly calling `display` with `OUTCOME=COMMITTED`),
- computing subtotal/tax/total inline — it must come from `api-price-order`,
- deciding fraud outcome itself — it must call `api-fraud-decision`,
- generating payment auth ids — it must call `api-authorize-payment`,
- writing `ROLLBACK_STAGES=NONE` without consulting `api-state-rollback-stages`.

A reviewer can prove this by replacing any sample value in `samples/cart.aura` and observing that subtotal, tax, total, fraud-score, and fraud-decision all shift accordingly while the contract keys/order stay identical.

## 5. How to run



Expected exit code: `0`. Stdout must match the 13-line contract exactly. Anything on stderr is a failure.

## 6. Implementation notes

- All state is held in association lists (`(cons (cons key value) rest)`), accessed with a small `assq` helper in `pipeline/state.aura`.
- `pipeline/registry.aura` keeps two alists: `runs` and `compensations`, mapping stage name (symbol) → function.
- Compensation order is reverse of execution: `saga/compensate.aura` calls `reverse` on `api-state-rollback-stages`.
- `payment/authorize.aura` returns a synthetic auth id built from `state` + current time-ish counter; the reference derives the same id deterministically from `order-id` + amount, so main never sees the literal.
- `fraud/score.aura` returns an integer score `0..100` derived from cart contents + amount. The decision module returns the symbol `'ACCEPT` or `'REJECT`.
