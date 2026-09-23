# mini-router — 3-file multi-file success predicate

Write a **three-file** Aura program (`table.aura` + `match.aura` + `main.aura`)
that implements a tiny HTTP-ish route table and prints exactly these lines
(each plus a trailing newline), **in this order**:

```
GET_SLASH=home
GET_API=api
GET_API_V1=api
GET_API_V2=api
POST_API=405
MISS=404
COUNT=5
```

## Semantics

| Line | Meaning |
|------|---------|
| `GET_SLASH=home` | `(route-lookup "GET" "/")` → `home` |
| `GET_API=api` | `(route-lookup "GET" "/api")` → `api` (exact) |
| `GET_API_V1=api` | `(route-lookup "GET" "/api/v1")` → `api` (**prefix** of `/api`) |
| `GET_API_V2=api` | `(route-lookup "GET" "/api/v2")` → `api` (same prefix rule; second prefix hit so one-shot hardcodes fail more often) |
| `POST_API=405` | `(route-lookup "POST" "/api")` → `405` (method not allowed for that path’s allowed methods, **or** an explicit POST handler returning `405`) |
| `MISS=404` | `(route-lookup "GET" "/nope")` → `404` (unknown) |
| `COUNT=5` | Number of lookups in `main` whose result is **not** `404`. In the printed scenario the five lines before `MISS` are resolved non-404 hits, so `COUNT=5`. Do **not** count registered routes; count live non-404 lookup results among the six scenario lookups. |

Routes to support:

- GET `/` → `home` (exact)
- GET `/api` → `api` (exact)
- GET `/api/v1` → `api` via **one prefix rule** (prefix `/api` for GET)
- GET `/api/v2` → `api` (same prefix rule)
- POST `/api` → `405`
- anything else → `404`

## Required structure (3 files)

- **`table.aura`** — route table data and register helpers. Must define
  `(define (route-register …) …)` (and typically a table init / `routes-init`
  or equivalent that registers the routes above).
- **`match.aura`** — must define `(define (route-lookup method path) …)` with
  exact match **and** one prefix rule so GET `/api/v1` resolves to `api`.
- **`main.aura`** — must **call** `(route-lookup …)` for the five scenario
  lookups and print the six lines (including `COUNT`). Do not hardcode only
  the six display strings without calling `route-lookup`.

Hardcoding all seven stdout lines in `main.aura` alone without
`route-register` / `route-lookup` defines is a fail.

No Python. Prefer `display` / `newline` / `set!` / `equal?` / `string-length` /
`substring` / lists / `if` / `let`.

## How multi-file runs under Aura (honest)

Aura's binary **natively** accepts multiple files on the CLI:

```bash
$AURA_BIN table.aura match.aura main.aura
```

Definitions from earlier files are visible to later ones. This project's
`verify.sh` uses **CLI multi-file** in that order — not a fake module system.

## Why stubs start wrong

`stub/*.aura` are intentionally broken (e.g. missing prefix so `GET_API_V1`
fails, and/or POST returns `api` instead of `405`) so aura-build's MiniMax
propose → Aura verify → repair loop has real 3-file work.
