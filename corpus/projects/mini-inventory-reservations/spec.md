# Inventory Reservation System — GOAL.md

## Overview

A miniature SKU reservation ledger implemented in Aura. The system tracks per-SKU stock levels, places time-limited `hold` reservations that expire after a TTL, releases reservations early on cancellation, applies restock events, and prevents oversells when concurrent reservations arrive for the same SKU. All state lives in-memory (alist + helper lists) within a single Aura process; "concurrency" is simulated by interleaving reservation attempts and checking invariants.

The program reads no input; the scenario is a fixed scripted sequence of API calls driven by `main.aura`. The final stdout contract lists measured counters and invariants (active holds, expired holds, restock totals, oversell attempts rejected, etc.).

## Stdout contract (KEY=value lines, in this exact order)



## Module table

| File | Required exported `define` forms |
|------|-----------------------------------|
| `state.aura` | `(make-store)`, `(store-stock s sku)`, `(store-set-stock! s sku n)`, `(store-adjust! s sku delta)`, `(store-ledger s)`, `(store-ledger-append! s entry)`, `(store-holds s)`, `(store-hold-add! s hold)`, `(store-hold-remove! s hid)`, `(store-active-count s sku)` |
| `time.aura` | `(now-ms)`, `(advance-ms! delta)`, `(set-clock! ms)` |
| `hold.aura` | `(make-hold id sku qty ttl-ms created-at)`, `(hold-id h)`, `(hold-sku h)`, `(hold-qty h)`, `(hold-expires-at h)`, `(hold-expired? h now)` |
| `reservation.aura` | `(api-reserve store sku qty now ttl-ms)`, `(api-release store hold-id)`, `(api-expire-sweep store now)`, `(api-active-holds store sku)` |
| `restock.aura` | `(api-restock store sku units reason at-ms)`, `(api-restock-count store)`, `(api-restock-units store)` |
| `oversell.aura` | `(api-attempt-reserve store sku qty now ttl-ms)`, `(oversell-rejected-count store)`, `(oversell-increment! store)` |
| `invariants.aura` | `(api-check-invariant store)`, `(api-assert-ok store)` |
| `concurrency.aura` | `(api-stress-reserve store requests now ttl-ms)`, `(stress-results results)` |
| `report.aura` | `(api-reservations-held store)`, `(api-reservations-expired store)`, `(api-reservations-released store)`, `(api-reservations-total store)`, `(api-stock-of store sku)`, `(api-final-active-holds store)`, `(api-ledger-entries store)` |
| `hash.aura` | `(api-hash-reservations-total total)`, `(api-hash-oversell-blocked blocked)`, `(api-hash-mix n)` |
| `scenario.aura` | `(run-scenario store)` — runs the scripted sequence and returns the final store + counters |
| `main.aura` | `(main)` — entry point: builds the store, runs the scenario, prints the 15 KEY=value lines in order |

## Scenario steps (driven by `run-scenario` in `scenario.aura`, invoked from `main.aura`)

The scenario runs a deterministic script against a freshly built store seeded with `SKU_A=40`, `SKU_B=10`, `SKU_C=5`, and `now=1000`.

1. **Reserve happy path** — call `api-attempt-reserve` for 5 units of `SKU_A` (TTL 500ms) twice, then 3 units of `SKU_B` once. Expect 3 successful reservations, 0 oversells.
2. **TTL expiry sweep** — `advance-ms!` to `now=1600` (past first hold's expiry), then call `api-expire-sweep`. Expect 1 hold expired, 1 unit of `SKU_A` returned to stock.
3. **Cancel/release** — release one still-active hold on `SKU_B` by hold-id via `api-release`. Expect 1 release, units returned.
4. **Restock events** — `api-restock SKU_A +10` (reason `shipment`), `api-restock SKU_B +3` (reason `return`), `api-restock SKU_C +2` (reason `manual`). Expect 3 restock events, 15 units added total.
5. **Oversell prevention** — call `api-attempt-reserve SKU_C qty=999` (must be rejected, oversell counter +1), then again `api-attempt-reserve SKU_C qty=999` (rejected again, oversell +1). Expect `OVERSELL_BLOCKED=2`.
6. **Concurrency stress** — call `api-stress-reserve` with a list of 7 mixed requests: 3 valid small reservations on `SKU_A`, 4 oversell attempts on `SKU_C`. Expect remaining valid reservations to succeed, oversells rejected. Increment counters accordingly so that final `RESERVATIONS_TOTAL=10` and `OVERSELL_BLOCKED=2` hold (combined with steps 1–5).
7. **Invariant check** — call `api-check-invariant`: sum of (initial stock + restock − fulfilled reservations + released/expired units back) must equal current stock across all SKUs. Expect `INVENTORY_INVARIANT_OK=true`.
8. **Report aggregation** — compute counters via `report.aura` APIs (held, expired, released, total, final stock of each SKU, active holds final, ledger entries).
9. **Hash summary** — feed `(api-hash-reservations-total total)` and `(api-hash-oversell-blocked blocked)` through `api-hash-mix` to produce deterministic integer digests printed as `HASH_*` lines.
10. **Print** — `main.aura` prints the 15 KEY=value lines in the exact order shown above.

## Anti-hardcode

`main.aura` MUST build the store, call `run-scenario`, and read every printed value through the module APIs (`api-stock-of`, `api-reservations-held`, `api-reservations-expired`, `api-reservations-released`, `api-reservations-total`, `api-final-active-holds`, `api-ledger-entries`, `api-hash-mix`, `api-check-invariant`). It must not embed numeric literals like `42`, `18`, `0`, `7`, `2`, `1`, `10`, `15`, `3`, `18` as raw `display` arguments — every value must come from a module API result. (The string `"true"` for the invariant line is produced by `api-check-invariant` returning a boolean that `main` renders.)

## How to run



All files are loaded into one shared top-level Aura image; `main.aura` triggers the scenario and prints the 15-line contract to stdout.
