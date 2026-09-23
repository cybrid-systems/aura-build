# mini-kv — success predicate

Write a small **Aura** program that implements a tiny in-memory key/value store
and prints exactly these lines (each plus a trailing newline):

```
GET_a=1
GET_b=2
MISS=nil
GET_c=3
```

## Semantics

| Line | Meaning |
|------|---------|
| `GET_a=1` | After `(kv-set "a" 1)`, `(kv-get "a")` → `1` |
| `GET_b=2` | After `(kv-set "b" 2)`, `(kv-get "b")` → `2` |
| `MISS=nil` | `(kv-get "z")` (or any unset key) → `nil` |
| `GET_c=3` | After `(kv-set "c" 3)`, `(kv-get "c")` → `3` |

Use a mutable association list (or equivalent) with `set!` so later gets see
earlier sets. Call order must be: set a, set b, get a, get b, get miss, set c,
get c (prints follow the four lines above).

## Required structure

- Must define `(define (kv-set …) …)` and `(define (kv-get …) …)` (names may be
  `kv-set!` / `kv-lookup` etc. **only if** they still match `kv-set` / `kv-get`
  as substrings in the define form — prefer exact `kv-set` / `kv-get`).
- Hardcoding only the four display literals without real `kv-set`/`kv-get`
  function definitions is a fail (`verify.sh` checks source + stdout).
- No Python. Prefer `display` / `newline` / `set!` / `cons` / `car` / `cdr` /
  `null?` / `equal?`.

## Why stub starts wrong

`stub.aura` intentionally has a broken store, wrong values, and missing
`kv-get` so aura-build’s MiniMax propose → Aura verify → repair loop has real
work (see `aura-build llm-dogfood --task kv` or `--project examples/projects/mini-kv`).
