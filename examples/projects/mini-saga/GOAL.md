# mini-saga — 10-file multi-file success predicate (magnitude jump)

Write a **ten-file** Aura program
(`idemp.aura` + `journal.aura` + `book.aura` + `pay.aura` + `ship.aura` +
`step.aura` + `compensate.aura` + `saga.aura` + `query.aura` + `main.aura`)
that implements a lightweight **travel-ish saga** (book → pay → ship) with
**compensate-on-failure** and **idempotency keys**, and prints exactly these
lines (each plus a trailing newline), **in this order**:

```
OK=committed
ST1=held/charged/sent
DUP=dup
ST1B=held/charged/sent
FAIL_PAY=aborted
ST2=cancelled/none/none
FAIL_SHIP=aborted
ST3=cancelled/refunded/none
COUNT=4
```

## Semantics (pure Aura — no Python)

| Op | File | Behavior |
|----|------|----------|
| `(idemp-init)` | idemp.aura | Clear seen keys |
| `(idemp-seen? key)` | idemp.aura | `#t` if key marked, else `#f` |
| `(idemp-mark key)` | idemp.aura | Remember key |
| `(journal-init)` | journal.aura | Clear journal |
| `(journal-append step status)` | journal.aura | Append `(step status)` |
| `(journal-last)` | journal.aura | Last entry or `"empty"` |
| `(journal-has? step status)` | journal.aura | `#t` if any entry matches |
| `(book-init)` / `(book-reserve key room)` / `(book-cancel key)` / `(book-state)` | book.aura | Reserve → `"ok"`\|`"dup"`\|`"fail"` (`fail` if room=`"full"`; `dup` if idemp seen). State: `"none"`\|`"held"`\|`"cancelled"` |
| `(pay-init)` / `(pay-charge key amount)` / `(pay-refund key)` / `(pay-state)` | pay.aura | Charge → `"ok"`\|`"dup"`\|`"fail"` (`fail` if amount=`"bad"` or `0`/`"0"`). State: `"none"`\|`"charged"`\|`"refunded"` |
| `(ship-init)` / `(ship-send key dest)` / `(ship-recall key)` / `(ship-state)` | ship.aura | Send → `"ok"`\|`"dup"`\|`"fail"` (`fail` if dest=`"blocked"`). State: `"none"`\|`"sent"`\|`"recalled"` |
| `(run-step name thunk-result)` | step.aura | `journal-append` name result; return result |
| `(compensate-from step)` | compensate.aura | fail@pay → `book-cancel`; fail@ship → `pay-refund` then `book-cancel`; fail@book → noop. Return `"comped"`\|`"noop"` |
| `(saga-init)` / `(saga-run sid room amount dest)` | saga.aura | Per-step idemp keys from `sid`; book→pay→ship; on first fail compensate-from that step, journal abort, return `"aborted"`; on success journal commit return `"committed"`. If journal already committed for `sid`, return `"dup"` (no double side-effects) |
| `(saga-status)` | query.aura | `book-state/pay-state/ship-state` joined by `/` |

## Scenario (what `main.aura` must do)

1. All inits (`idemp`, `journal`, `book`, `pay`, `ship`, `saga`)
2. `(saga-run "s1" "r1" "10" "home")` → success → `OK=committed`
3. `ST1=` `(saga-status)` → `held/charged/sent`
4. `(saga-run "s1" "r1" "10" "home")` again → `DUP=dup` (idempotent)
5. `ST1B=` status still `held/charged/sent` (no double side effects)
6. Re-init book/pay/ship/idemp/journal/saga for a clean slate (document: main calls full reinits)
7. `(saga-run "s2" "r2" "bad" "home")` → pay fails → compensate book → `FAIL_PAY=aborted`, `ST2=cancelled/none/none`
8. Re-init again
9. `(saga-run "s3" "r3" "10" "blocked")` → ship fails → refund+cancel → `FAIL_SHIP=aborted`, `ST3=cancelled/refunded/none`
10. `COUNT=` number among `{OK, DUP, FAIL_PAY, FAIL_SHIP}` that are in `{committed, dup, aborted}` — all 4 → `COUNT=4`

## Required structure (10 files)

- **`idemp.aura`** — `(define (idemp-init) …)`, `(define (idemp-seen? key) …)`, `(define (idemp-mark key) …)`
- **`journal.aura`** — `(define (journal-init) …)`, `(define (journal-append step status) …)`, `(define (journal-last) …)`, `(define (journal-has? step status) …)`
- **`book.aura`** — book-init / book-reserve / book-cancel / book-state
- **`pay.aura`** — pay-init / pay-charge / pay-refund / pay-state
- **`ship.aura`** — ship-init / ship-send / ship-recall / ship-state
- **`step.aura`** — `(define (run-step name thunk-result) …)`
- **`compensate.aura`** — `(define (compensate-from step) …)`
- **`saga.aura`** — `(define (saga-init) …)`, `(define (saga-run sid room amount dest) …)`
- **`query.aura`** — `(define (saga-status) …)`
- **`main.aura`** — must **call** `saga-run` and `saga-status` (and the scenario) — not bare hardcoded display lines alone

Hardcoding all nine stdout lines in `main.aura` alone without the defines
split across files is a fail.

No Python. Prefer `display` / `newline` / `set!` / `equal?` / `if` / `let` /
`begin` / `cond` / `and` / `or` / `string-append` / `member`.

## How multi-file runs under Aura (honest)

```bash
$AURA_BIN idemp.aura journal.aura book.aura pay.aura ship.aura step.aura compensate.aura saga.aura query.aura main.aura
```

Definitions from earlier files are visible to later ones. This project's
`verify.sh` uses **CLI multi-file** in that order — not a fake module system.

## Why stubs start wrong

`stub/*.aura` are intentionally broken (always committed, no compensate, dup
mutates state, ship fail doesn't refund, COUNT wrong) so aura-build's MiniMax
propose → Aura verify → repair loop has real **10-file** saga work.
