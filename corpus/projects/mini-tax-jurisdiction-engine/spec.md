# Mini Tax Jurisdiction Engine — GOAL.md

## Overview
A toy but realistic **tax-jurisdiction engine** for an invoice of mixed line items.
The engine resolves, per line, the **applicable tax** by composing four inputs:

1. **Nexus rules** — where the seller has tax obligations (state + county + city).
2. **Product tax codes** — what *kind* of good (groceries, apparel, digital, SaaS, etc.).
3. **Customer exemption certificates** — which jurisdictions the customer is exempt in.
4. **Origin-vs-destination logic** — origin-based states (e.g. OR, NH) skip destination tax; destination states apply tax where the ship-to sits.

The engine applies **rounding** (banker/half-even per line, then sum; half-up at invoice total)
and emits **audit-grade** per-line breakdowns that show every step of the resolution.

Everything is in-memory, list/alist-based, deterministic, and reproducible from a single seed of facts.

---

## 2. Exact stdout contract

The program prints exactly the following 14 `KEY=value` lines, in this order, separated by `\n`, with a final newline:



Values **must** be derived by calling the module APIs — never hard-coded.
The `AUDIT_HASH` is a short hex string computed by hashing the per-line breakdown list
(so it changes if any input fact changes; same inputs → same hash).

---

## 3. Module table

All files are loaded together on a single Aura CLI invocation, sharing one top-level environment.
Each file exposes a small, named set of `define (api …)` forms.

| # | File | Public API `(define (api …) …)` | Purpose |
|---|------|---------------------------------|---------|
| 1 | `facts_nexus.aura` | `(api load-nexus-rules)` → list of nexus alists | Seller's nexus footprint per state/county/city |
| 2 | `facts_products.aura` | `(api load-product-tax-codes)` → alist of code→category | PTC → taxability category (groceries/apparel/digital/SaaS/tangible) |
| 3 | `facts_exemptions.aura` | `(api load-exemption-certs)` → list of cert alists | Customer exemption certificates (jurisdiction + reason) |
| 4 | `facts_jurisdictions.aura` | `(api load-jurisdiction-rates)` → alist jid→rate-bps | Per-jurisdiction composite rate (state+local) in basis points |
| 5 | `facts_customers.aura` | `(api load-customer)` → alist | Customer record (id, ship-to, exemption-cert-ids) |
| 6 | `facts_invoice.aura` | `(api load-invoice)` → alist | Invoice (id, lines: list of alists) |
| 7 | `resolve_jurisdiction.aura` | `(api resolve-jurisdiction ship-to nexus)` → jid or `#f` | Origin-vs-destination pick; `#f` if no nexus |
| 8 | `apply_exemption.aura` | `(api apply-exemption jid certs ptc)` → `#t`/`#f` | Cert covers this jurisdiction *and* product class? |
| 9 | `compute_line_tax.aura` | `(api compute-line-tax line nexus rates certs origin-states)` → alist | Per-line tax result with full breakdown |
| 10 | `round_money.aura` | `(api round-line cents)` `(api round-invoice cents)` | Half-even per line, half-up at invoice total |
| 11 | `audit_log.aura` | `(api make-audit-hash breakdowns)` `(api append-line-log! line)` | Mutable audit log via `set!` on a global list |
| 12 | `invoice_aggregate.aura` | `(api aggregate-invoice line-results)` → summary alist | Counts + totals across all lines |
| 13 | `main.aura` | `(define (run) …)` | Orchestrates everything, prints the 14 KEY=… lines |

**Constraint:** each API is ≤ ~30 lines; all state is in-memory lists + one mutable audit log.

---

## 4. Scenario steps (executed by `main.aura`)

1. **Load facts** by calling the 6 `facts_*` APIs.
2. **Build the per-line resolver** once: `origin-states = (filter origin-based? nexus-rules)`.
3. **For each invoice line**, call `compute-line-tax` with the line's PTC, qty, unit-price, ship-to (from customer), nexus rules, rates alist, and exemption certs.
4. Inside `compute-line-tax`:
   - `resolve-jurisdiction` → jid (or `#f` ⇒ tax=0).
   - If origin-state, force tax=0 even if jurisdiction resolves (origin overrides destination).
   - `apply-exemption` jid certs ptc → if `#t`, tax=0 with reason "EXEMPT_CERT".
   - Else compute `floor(unit_price * qty * rate_bps / 10000)`, then `round-line`.
   - Append a structured breakdown alist to the global audit log via `append-line-log!`.
5. **Aggregate** with `aggregate-invoice` → counts + subtotal/tax totals.
6. **Round the invoice tax total** with `round-invoice`; grand total = subtotal + tax_total.
7. **Hash the audit log** with `make-audit-hash` (fold over breakdown strings → running 64-bit mix → hex).
8. **Print** the 14 `KEY=value` lines in the exact order above.
9. Final key `RESOLUTION_OK` is `#t` iff every line's `(status)` is one of `#t / "OK" / "EXEMPT" / "ZERO_RATE" / "NO_NEXUS"` (sanity gate).

---

## 5. Anti-hardcode

`main.aura` **must not**:
- embed any of the 14 printed values as string literals,
- skip the per-line `compute-line-tax` loop,
- reuse a precomputed breakdown.

It **must**:
- call all 12 module APIs at least once,
- derive `TAX_TOTAL_CENTS` from the sum of rounded per-line taxes,
- derive `AUDIT_HASH` from `make-audit-hash` over the audit log,
- derive `TAXABLE_LINES`/`EXEMPT_LINES`/`ZERO_TAX_LINES` by counting statuses from `compute-line-tax` results.

A reviewer can flip a rate in `facts_jurisdictions.aura` and observe all 14 keys shift consistently.

---

## 6. How to run



Expected exit code: `0`. Output is the 14 `KEY=value` lines on stdout, nothing on stderr.

---
