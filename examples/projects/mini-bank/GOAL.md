# mini-bank — multi-file success predicate

Write a **multi-file** Aura program (`lib.aura` + `main.aura`) that implements
tiny account helpers and prints exactly these lines (each plus a trailing newline):

```
A=100
B=50
A2=70
B2=80
OK=1
```

## Semantics

| Line | Meaning |
|------|---------|
| `A=100` | Starting balance of account A |
| `B=50` | Starting balance of account B |
| `A2=70` | After transfer 30 from A→B, A's balance |
| `B2=80` | After transfer, B's balance |
| `OK=1` | `1` if `A2+B2 == A+B` (conservation), else `0` |

Start A=100, B=50. Transfer 30 from A to B: `(debit "A" 30)` then `(credit "B" 30)`
(or a `transfer` helper that calls them). Then print A2/B2 from live balances and
OK from conservation.

## Required structure (multi-file)

- **`lib.aura`** must define `(define (credit …) …)`, `(define (debit …) …)`,
  and `(define (balance …) …)` (optionally also `transfer`).
- **`main.aura`** must call those helpers (not hardcode only the five display
  lines without lib defines).
- Hardcoding the five stdout lines in `main.aura` alone without lib defines is a fail.
- No Python. Prefer `display` / `newline` / `set!` / `equal?` / `+` / `-`.

## How multi-file runs under Aura (honest)

Aura's binary **natively** accepts multiple files on the CLI:

```bash
$AURA_BIN lib.aura main.aura
```

Definitions from earlier files are visible to later ones. Aura also supports
`(load "lib.aura")` from `main.aura`. This project's `verify.sh` uses **CLI
multi-file** (`aura lib.aura main.aura`) — not a fake module system.

## Why stubs start wrong

`stub/lib.aura` and `stub/main.aura` are intentionally broken so aura-build's
MiniMax propose → Aura verify → repair loop has real multi-file work.
