# mini-calc — success predicate

Write a small **Aura** program that defines named helpers and prints exactly
these three lines (each plus a trailing newline):

```
ADD=7
MUL=12
MIX=17
```

## Semantics

| Line | Meaning |
|------|---------|
| `ADD=7` | `(add 3 4)` → `3+4` |
| `MUL=12` | `(mul 3 4)` → `3*4` |
| `MIX=17` | `(add (mul 3 4) 5)` → `(3*4)+5` |

## Required structure

- Must define `(define (add a b) …)` and `(define (mul a b) …)` (or equivalent
  two-arg named functions) and **call** them when printing.
- Hardcoding only the three display literals without `add`/`mul` definitions is
  a fail (`verify.sh` checks source + stdout).
- No Python. Prefer `display` / `newline` / `+` / `*`.

## Why stub starts wrong

`stub.aura` intentionally has a broken `add`, missing `mul`, and wrong MIX so
aura-build’s MiniMax propose → Aura verify → repair loop has real work (see
`aura-build llm-dogfood --task calc`).
