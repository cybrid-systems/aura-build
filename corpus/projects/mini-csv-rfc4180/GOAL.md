# GOAL.md — mini-csv-rfc4180

## Overview

A small, streaming RFC 4180–compliant CSV parser written in Aura. The library
takes an input port (or a string source) and yields one logical row at a time,
where each row is a list of typed cells (numbers become numbers, `#t`/`#f`
strings become booleans, everything else stays a string). It correctly handles:

- Quoted fields: `"hello, world"`
- Embedded delimiters inside quoted fields
- Escaped double-quotes inside quoted fields: `"he said ""hi"""`
- Both `\r\n` and `\n` line endings (with optional trailing newline)
- UTF-8 BOM stripping at start of stream
- Empty fields between delimiters
- Configurable delimiter (default `,`)

The parser exposes a **pull-style** iterator: each call to `csv-next-row`
returns either a row (list of cells) or the sentinel `'eof` when the stream
is exhausted. This lets callers process arbitrarily large inputs without
materializing all rows in memory.

The CLI scenario parses a fixture file containing tricky RFC 4180 cases
(quotes, embedded delimiters, escaped quotes, CRLF, BOM, blank trailing row,
mixed types) and prints a fixed set of `KEY=value` lines reporting the row
count, per-row cell counts, and a few representative cell values to prove the
parser actually walked the stream through the public APIs.

---

## Stdout contract (exact order)

The scenario must print exactly these 15 lines, in this order, with the given
keys. Values are computed at runtime by calling the module APIs — see
*Anti-hardcode* below.



Notes:
- `ROW1_C0=foo` and `ROW1_C2=42` prove type coercion of cell 2 into a number
  (the parser returns the number `42`, then `(number->string …)` renders it).
- `ROW4_C3=2.5` proves fractional-number coercion.
- `ROW5_C0=` is an empty field (still a non-empty row of length 2).
- `ROW6_C0=true` is a boolean coerced from the literal string `"true"`.

---

## Module table

All files are loaded in order on a single Aura CLI invocation, sharing one
top-level environment.

| File | Required `(define (api …))` forms |
|------|------------------------------------|
| `csv-types.aura` | `(define-record row cells), (define (make-row cells)), (define (row-cells r)), (define (cell-value c)), (define (cell-kind c) -> 'number|'bool|'string), (define eof-sentinel), (define (eof? v))` |
| `csv-util.aura` | `(define (csv-bom? ch)), (define (csv-strip-bom port)), (define (csv-peek port)), (define (csv-read-char port)), (define (csv-next-line port))` |
| `csv-lexer.aura` | `(define (csv-open s|port :key delimiter)), (define (lexer-state l)), (define (lexer-exhausted? l)), (define (lexer-next-cell l) -> cell|'eof), (define (lexer-next-row l) -> row|'eof)` |
| `csv-coerce.aura` | `(define (csv-coerce str) -> cell)` |
| `csv-iterator.aura` | `(define (make-csv-iter source :key delimiter)), (define (iter-next iter) -> row|'eof), (define (iter-rest iter) -> list-of-rows), (define (iter-count iter) -> n)` |
| `csv-fixture.aura` | `(define csv-fixture-text), (define (csv-fixture-port))` |
| `csv-report.aura` | `(define (csv-report-rows rows)), (define (csv-format-key prefix idx n) -> string)` |
| `main.aura` | (entry point — uses APIs above; no business logic inline beyond orchestration) |

`main.aura` is the final file loaded. Earlier files only **define** APIs;
they must not print anything.

---

## Scenario steps (main.aura)

1. Get the fixture text via `(csv-fixture-text)` and open a parser via
   `(make-csv-iter (csv-fixture-port) :delimiter #\,)`.
2. Use `(iter-rest iter)` to materialize the full row list (small fixture,
   streaming contract is still respected because the lexer is pull-based).
3. Sanity check: assert `(length rows) = 6` via `(iter-count (make-csv-iter …))`
   on a *fresh* iterator — proves the iterator is reusable, not a one-shot
   hack.
4. For each row index `0..5`, use `(row-cells (list-ref rows i))` to get the
   cell list, then `(length …)` and targeted `(cell-value …)` lookups via
   `(list-ref … j)`.
5. Print the 15 `KEY=value` lines in the exact order above using
   `(csv-report-rows rows)` plus the helpers in `csv-report.aura`.
6. A row whose length is 1 must print `ROW3_LEN=1` and `ROW3_C0=he said "hi"`,
   proving escaped-quote handling through the public API path.
7. The boolean row must surface as the string `"true"` (coercion is done by
   `csv-coerce`, the value extracted by `cell-value`).

`main.aura` MUST go through the module APIs to obtain every value it prints.
No literal row lists, no pre-baked strings.

---

## Anti-hardcode

`main.aura` is not allowed to:

- Embed the fixture as a literal Aura string and slice it.
- Construct row lists directly with `(list …)` to mimic parser output.
- Print any of the 15 expected `KEY=value` lines using literal values known
  from this file.

The reference check will mutate the fixture text (swap the order of two rows,
change the embedded delimiter phrase, flip CRLF↔LF) and confirm the printed
`KEY=value` block still matches the new fixture. Anything hardcoded will be
caught. The parser’s correctness is what’s under test, not its test data.

---

## How to run



Expected exit status: `0`. stdout contains exactly the 15 `KEY=value` lines
listed above, in order, with a trailing newline.

---
