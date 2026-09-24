# mini-json-tok — Zero-copy JSON Tokenizer & Parser

A small Aura project that hand-rolls a **zero-copy UTF-8 JSON tokenizer** plus a **tolerant parser** that emits a **structural index** and **streaming events**, with optional **lenient recovery** of trailing garbage. Everything is in-memory; no I/O, no FFI — just lists, numbers, strings, and recursion.

The project is split across 11 `.aura` source files (10 library modules + `main.aura`). `main.aura` is a scenario that feeds several JSON snippets to the library, asks the tokenizer / parser / stream / recovery APIs to do work, and then prints a fixed set of `KEY=value` lines describing the observed behaviour. **All numbers and counts in the printed output come from runtime API results, not literal constants.**

## 1. Stdout contract (exact order, KEY=value)

The scenario must print exactly these 17 keys, in this order, one per line, `KEY=value`:



All values are non-negative integers (counts) or `#t`/`#f` for the booleans. Values are computed by calling the library APIs from `main.aura` — not hard-coded.

## 2. Module table

All files are loaded on one Aura CLI invocation, in the listed order, before `main.aura`:

| # | File | Required exported `define` forms (API surface) |
|---|------|------------------------------------------------|
| 1 | `utf8.aura` | `(define (utf8-bom-skip s i))`, `(define (utf8-validate s))`, `(define (utf8-byte-len b))` |
| 2 | `json-lex.aura` | `(define (lex-tokenize src))`, `(define (token-kind token))`, `(define (token-span token))`, `(define (token-value token))` |
| 3 | `json-ast.aura` | `(define (parse-json src))`, `(define (ast-kind node))`, `(define (ast-children node))`, `(define (ast-value node))` |
| 4 | `json-index.aura` | `(define (build-index node))`, `(define (index-depth idx))`, `(define (index-count idx kind))`, `(define (index-walk idx proc))` |
| 5 | `json-stream.aura` | `(define (stream-events src))`, `(define (event-kind ev))`, `(define (event-path ev))`, `(define (event-depth ev))` |
| 6 | `json-recover.aura` | `(define (recover-lenient src))`, `(define (recovery-status r))`, `(define (recovery-bytes-used r))`, `(define (recovery-ast r))` |
| 7 | `json-path.aura` | `(define (path-equal? a b))`, `(define (path-prepend p k))`, `(define (path-key p))`, `(define (path-index p))` |
| 8 | `json-errors.aura` | `(define (make-error code pos msg))`, `(define (error? v))`, `(define (error-code e))`, `(define (error-pos e))` |
| 9 | `counts.aura` | `(define (count-by-kind tokens kinds))`, `(define (sum lst))`, `(define (every? p lst))`, `(define (max-depth nodes))` |
| 10 | `scenario.aura` | `(define (run-scenario))` — orchestrates everything, returns an alist of results |
| 11 | `main.aura` | entry point: calls `(run-scenario)`, prints the 17 keys above |

## 3. Scenario steps (driving the APIs from `scenario.aura`)

`scenario.aura` builds a list of JSON samples:

1. **Well-formed doc A** — `{"name":"ada","age":36,"skills":["math","cs"]}` (object → array → strings/number).
2. **Well-formed doc B** — `[1,2,3,4,5]` (flat array of numbers).
3. **Well-formed doc C** — `{"nested":{"a":1,"b":[true,false,null,"end"]}}` (deeper nesting, mixed types).
4. **Garbage doc** — `{"x":1}garbage tail` (valid prefix, trailing junk).
5. **Truncated doc** — `{"only":"half` (unterminated string, no closing brace).

For each step, `scenario.aura` calls the APIs (no string literals of expected numbers):

- **`utf8.aura`** — runs `utf8-byte-len` on a sample of leading bytes; `utf8-bom-skip` on `src`; `utf8-validate` returns `#t`/`#f` (used to gate parsing).
- **`json-lex.aura`** — tokenizes doc A; counts tokens by kind via `counts.aura:count-by-kind`.
- **`json-ast.aura`** — parses A, B, C; counts successes/failures via `ast-kind`/`ast-children`.
- **`json-index.aura`** — builds the structural index for C; `index-depth` → max depth; `index-count` for `'object` keys and `'array` elements.
- **`json-stream.aura`** — streams events over A; total event count; presence booleans for `'string`/`'number`/`'bool`/`'null` event kinds.
- **`json-recover.aura`** — runs `recover-lenient` on the garbage doc and the truncated doc; checks `recovery-status` for `'recovered` vs `'truncated` and increments the matching counter.
- **`counts.aura`** — `sum` and `every?` are used internally to aggregate token-kind lists.

Finally `run-scenario` returns an alist `((TOK_KIND_TOTAL . n) … (TOK_LENIENT_TRUNCATED . n))` and `main.aura` walks it once with `display` to emit the 17 lines in the exact order above.

## 4. Anti-hardcode checklist

`main.aura` and `scenario.aura` do **not**:

- embed any of the 17 expected numeric values as literals,
- print any `KEY=` line that wasn't produced by an API call,
- skip APIs — every module listed in §2 is exercised at least once.

`main.aura` only does:
1. `(define results (run-scenario))` — pulls the alist from `scenario.aura`.
2. walks `results` in the fixed key order, calling `(display key)` `(display "=")` `(display (cdr (assq key results)))` `(newline)` for each of the 17 keys.

Because the values are produced by recursive tokenizers / parsers over real JSON strings, any change to the lexer or AST walker changes the printed counts.

## 5. How to run



Expected output: exactly 17 lines, each `KEY=value`, in the order listed in §1. A separate Python reference implementation measures the values; this Aura scenario must match.
