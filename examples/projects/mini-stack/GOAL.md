# mini-stack — success predicate

Write a small **Aura** program that implements a tiny mutable stack and prints
exactly these lines (each plus a trailing newline):

```
TOP=30
POP=30
TOP2=20
SIZE=2
EMPTY=0
```

## Semantics

| Line | Meaning |
|------|---------|
| `TOP=30` | After `(stack-push 10)`, `(stack-push 20)`, `(stack-push 30)`, `(stack-top)` → `30` |
| `POP=30` | `(stack-pop)` returns the popped value `30` |
| `TOP2=20` | After the pop, `(stack-top)` → `20` |
| `SIZE=2` | `(stack-size)` → `2` (stack still holds 10, then 20) |
| `EMPTY=0` | `(stack-empty)` → `0` if non-empty, `1` if empty — still non-empty → `0` |

Start from an empty stack. Call order must be: push 10, push 20, push 30, then
top → print TOP; pop → print POP; top → print TOP2; size → print SIZE;
empty → print EMPTY.

## Required structure

- Must define `(define (stack-push …) …)`, `(define (stack-pop …) …)`,
  `(define (stack-top …) …)`, and `(define (stack-size …) …)` (names may vary
  slightly but `verify.sh` / `dogfood.json` `source_res` check these substrings).
- Optionally `(define (stack-empty …) …)` (or inline `null?` → 0/1); prefer a
  named helper.
- Hardcoding only the five display literals without real stack function
  definitions is a fail (`verify.sh` checks source + stdout).
- No Python. Prefer `display` / `newline` / `set!` / `cons` / `car` / `cdr` /
  `null?` / recursive length.

## Why stub starts wrong

`stub.aura` intentionally has a broken stack, wrong values, and missing
`stack-pop` / `stack-top` / `stack-size` so aura-build’s MiniMax propose → Aura
verify → repair loop has real work (see `aura-build llm-dogfood --project
examples/projects/mini-stack` or `--task stack`).
