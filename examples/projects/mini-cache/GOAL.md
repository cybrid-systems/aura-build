# mini-cache — 3-file multi-file success predicate

Write a **three-file** Aura program (`store.aura` + `ops.aura` + `main.aura`)
that implements a tiny in-memory string→string cache with optional TTL and
prints exactly these lines (each plus a trailing newline), **in this order**:

```
GET_A=1
GET_MISS=miss
GET_B=2
TTL_EXPIRED=miss
COUNT=2
```

## Semantics (tick model — pick this one)

Global integer `tick` starts at 0 after `(cache-init)`.

| Op | Behavior |
|----|----------|
| `(cache-init)` | Reset store and `tick` to 0 |
| `(cache-set key val ttl)` | Store `(val . expire-tick)`. If `ttl` is `0`, expire-tick is `#f` (forever). If `ttl > 0`, expire-tick = `current-tick + ttl`. |
| `(cache-tick n)` | `(set! tick (+ tick n))` |
| `(cache-get key)` | Return value if key present and (expire-tick is `#f` **or** `current-tick < expire-tick`); else `"miss"` |

| Line | Meaning |
|------|---------|
| `GET_A=1` | forever key `"a"` → `"1"` |
| `GET_MISS=miss` | unknown key → `"miss"` |
| `GET_B=2` | key `"b"` with ttl=2 still live → `"2"` |
| `TTL_EXPIRED=miss` | after `(cache-tick 2)`, `"b"` expired → `"miss"` |
| `COUNT=2` | Among the **four** gets above, how many are **not** `"miss"` → expect 2 (`a` and first `b`) |

## Required structure (3 files)

- **`store.aura`** — must define `(define (cache-init) …)` and
  `(define (cache-set key val ttl) …)`.
- **`ops.aura`** — must define `(define (cache-get key) …)` and
  `(define (cache-tick n) …)` (or equivalent explicit tick advance used by main).
- **`main.aura`** — must **call** `cache-set` / `cache-get` / `cache-tick` for the
  scenario below (not bare hardcoded display lines alone):
  1. `(cache-init)`
  2. `(cache-set "a" "1" 0)` → forever
  3. `(cache-set "b" "2" 2)` → expires after 2 ticks
  4. print `GET_A=` `(cache-get "a")` → `1`
  5. print `GET_MISS=` `(cache-get "nope")` → `miss`
  6. print `GET_B=` `(cache-get "b")` → `2`
  7. `(cache-tick 2)` then print `TTL_EXPIRED=` `(cache-get "b")` → `miss`
  8. `COUNT=` number of the four gets that are NOT `miss` → `2`

Hardcoding all five stdout lines in `main.aura` alone without
`cache-init` / `cache-set` / `cache-get` / `cache-tick` defines is a fail.

No Python. Prefer `display` / `newline` / `set!` / `equal?` / `assoc` /
lists / `if` / `let` / `car` / `cdr`.

## How multi-file runs under Aura (honest)

Aura's binary **natively** accepts multiple files on the CLI:

```bash
$AURA_BIN store.aura ops.aura main.aura
```

Definitions from earlier files are visible to later ones. This project's
`verify.sh` uses **CLI multi-file** in that order — not a fake module system.

## Why stubs start wrong

`stub/*.aura` are intentionally broken (e.g. no TTL expiry so `TTL_EXPIRED`
stays live, and/or wrong `COUNT`) so aura-build's MiniMax propose → Aura
verify → repair loop has real 3-file work.
