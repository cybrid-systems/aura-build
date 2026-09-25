# Checkout Saga Orchestrator — GOAL.md

## Overview
A toy multi-file Aura program that orchestrates a 5-step checkout **saga** with **compensating actions**. The saga runs the steps `auth → inventory-hold → payment-auth → payment-capture → fulfillment-kickoff` in order. Each step is an **idempotent handler** keyed by `saga_id`. If any step fails, previously completed steps are **rolled back in reverse order** by calling their `compensate_*` handlers. Final state of each service (`order`, `payment`, `inventory`, `fulfillment`) is reported alongside the saga status (`COMPLETED` / `COMPENSATED` / `FAILED`). Persistent saga state is simulated via an in-memory alist journal; idempotency is enforced via a `(already-done? saga_id step)` lookup.

## Stdout Contract (exact lines, in order)



## Module Table

| File | Required `(define (api …))` forms |
|---|---|
| `state.aura` | `(make-journal)`, `(journal-record! j saga_id step)`, `(already-done? j saga_id step)`, `(saga-state j saga_id)` |
| `ids.aura` | `(make-id-gen)`, `(next-id gen prefix)` |
| `handlers.aura` | `(step-auth saga_id)`, `(compensate-auth saga_id)`, `(step-inventory-hold saga_id)`, `(compensate-inventory-hold saga_id)`, `(step-payment-auth saga_id)`, `(compensate-payment-auth saga_id)`, `(step-payment-capture saga_id)`, `(compensate-payment-capture saga_id)`, `(step-fulfillment-kickoff saga_id)`, `(compensate-fulfillment-kickoff saga_id)` |
| `services.aura` | `(svc-order saga_id)`, `(svc-inventory saga_id)`, `(svc-payment saga_id)`, `(svc-fulfillment saga_id)` |
| `compensator.aura` | `(rollback-completed! j saga_id completed-steps)`, `(build-audit-trail j saga_id)` |
| `orchestrator.aura` | `(run-saga j id-gen failure-step)`, `(saga-status j saga_id)` |
| `main.aura` | `(run main args)` — executes one saga with injectable failure point, calls `run-saga`, then prints every KEY line above |

(8 source files total; `main.aura` orchestrates and prints.)

## Scenario Steps (`main.aura`)

1. Create a journal: `(define j (make-journal))`.
2. Create an id generator: `(define g (make-id-gen))`.
3. Pull the failure point from `args` (default = `#f`, meaning happy path).
4. Call `(run-saga j g failure-step)` — this iterates the 5 steps in order; for each step it:
   - calls `(journal-record! j saga_id step-name)`,
   - guards with `(already-done? j saga_id step-name)` for idempotency,
   - invokes the matching `(step-…)` handler from `handlers.aura`,
   - on failure, populates `completed-steps` and asks `(rollback-completed! …)` to invoke each `compensate-…` in reverse.
5. Call `(saga-status j saga_id)` and `(build-audit-trail j saga_id)` to compute display values.
6. Compute `ORDER_STATE`, `PAYMENT_STATE`, `INVENTORY_HOLD_STATE`, `FULFILLMENT_STATE` by asking each `services.*` view function (NOT hardcoded — derived from journal + service state).
7. Print every KEY line in the exact order above.

## Anti-Hardcode
`main.aura` must:
- derive `ORDER_STATE`, `PAYMENT_STATE`, `INVENTORY_HOLD_STATE`, `FULFILLMENT_STATE` by reading the journal / service views (not by string-matching expected output),
- derive `SAGA_STATUS` from `(saga-status …)`, not from a literal,
- derive `STEP_AUDIT` from `(build-audit-trail …)`, not from a quoted list,
- count `COMPLETED_STEPS` / `COMPENSATED_STEPS` by walking the journal / rollback log.

A test that monkey-patches no failure still must observe `SAGA_STATUS=COMPLETED` only because `run-saga` actually advanced the journal through all 5 handlers.

## How to Run

Pass an optional failure step as argv-1:
