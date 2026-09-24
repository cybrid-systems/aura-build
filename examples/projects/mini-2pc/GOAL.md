# mini-2pc — 7-file multi-file success predicate (magnitude jump)

Write a **seven-file** Aura program
(`log.aura` + `part-a.aura` + `part-b.aura` + `vote.aura` + `coord.aura` +
`recover.aura` + `main.aura`) that implements a lightweight **two-phase
commit** over two in-memory participants with a coordinator and a write-ahead
decision log, and prints exactly these lines (each plus a trailing newline),
**in this order**:

```
RUN1=commit
STATE1=committed
RUN2=abort
STATE2=aborted
LOG=abort
RECOVER=aborted
POISON=abort
COUNT=5
```

## Semantics (pure Aura — no Python)

| Op | File | Behavior |
|----|------|----------|
| `(log-init)` | log.aura | Clear decision log |
| `(log-append decision)` | log.aura | Append decision string (`"commit"` / `"abort"`) |
| `(log-last)` | log.aura | Last decision, or `"empty"` if none |
| `(a-init)` | part-a.aura | Participant A → `"idle"` |
| `(a-prepare tx payload)` | part-a.aura | If payload is `"poison"` → `"no"` (stay idle). Else → prepared + `"yes"` |
| `(a-commit tx)` / `(a-abort tx)` | part-a.aura | Set state `"committed"` / `"aborted"` |
| `(a-state)` | part-a.aura | `"idle"` \| `"prepared"` \| `"committed"` \| `"aborted"` |
| `(b-*)` | part-b.aura | Same with `b-*`; refuse prepare if payload is `"deny-b"` |
| `(collect-votes tx payload)` | vote.aura | Call a-prepare + b-prepare; `"commit"` iff both `"yes"`, else `"abort"` |
| `(coord-init)` | coord.aura | Coordinator reset (no-op ok) |
| `(coord-run tx payload)` | coord.aura | Collect votes; on commit: log-append `"commit"`, a-commit, b-commit; else log-append `"abort"`, a-abort, b-abort; **return** decision string |
| `(recover-from-log)` | recover.aura | If log-last is commit and a part still prepared → finish commit; if abort → finish abort. Return `"committed"` \| `"aborted"` \| `"idle"` based on both parts agreeing after apply |

## Scenario (what `main.aura` must do)

1. `(log-init)`; `(a-init)`; `(b-init)`; `(coord-init)`
2. `(coord-run "t1" "ok")` → both prepare yes → commit path → print `RUN1=` → `commit`
3. `STATE1=` — if both `(a-state)` and `(b-state)` are `committed` then `committed` else `bad` → `committed`
4. `(coord-run "t2" "deny-b")` → b votes no → abort → `RUN2=abort`
5. `STATE2=` both aborted → `aborted`
6. `LOG=` `(log-last)` → `abort`
7. `(recover-from-log)` → after abort path, report `aborted` → `RECOVER=aborted`
8. Re-init parts + coord, then `(coord-run "t3" "poison")` → a refuses → `POISON=abort`
9. `COUNT=` among the seven printed values `{RUN1,STATE1,RUN2,STATE2,LOG,RECOVER,POISON}`, how many are exactly the string `abort` or `aborted`
   → RUN2, STATE2, LOG, RECOVER, POISON → **5**

## Required structure (7 files)

- **`log.aura`** — `(define (log-init) …)`, `(define (log-append decision) …)`, `(define (log-last) …)`
- **`part-a.aura`** — `(define (a-init) …)`, `(define (a-prepare tx payload) …)`, `(define (a-commit tx) …)`, `(define (a-abort tx) …)`, `(define (a-state) …)`
- **`part-b.aura`** — same with `b-*` prefixes; refuse `"deny-b"`
- **`vote.aura`** — `(define (collect-votes tx payload) …)`
- **`coord.aura`** — `(define (coord-init) …)`, `(define (coord-run tx payload) …)`
- **`recover.aura`** — `(define (recover-from-log) …)`
- **`main.aura`** — must **call** `coord-run` / `recover-from-log` / `a-state` / `b-state` / `log-last` (and the scenario) — not bare hardcoded display lines alone

Hardcoding all eight stdout lines in `main.aura` alone without the defines
split across files is a fail.

No Python. Prefer `display` / `newline` / `set!` / `equal?` / `if` / `let` /
`begin` / `cond` / `and` / `or`.

## How multi-file runs under Aura (honest)

```bash
$AURA_BIN log.aura part-a.aura part-b.aura vote.aura coord.aura recover.aura main.aura
```

Definitions from earlier files are visible to later ones. This project's
`verify.sh` uses **CLI multi-file** in that order — not a fake module system.

## Why stubs start wrong

`stub/*.aura` are intentionally broken (always commit, ignore deny-b/poison,
log never updates, recover always idle, COUNT wrong) so aura-build's MiniMax
propose → Aura verify → repair loop has real **7-file** 2PC work.
