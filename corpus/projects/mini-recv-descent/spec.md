# Mini-Recv-descent — Recursive Descent Parser

A small, hand-written recursive-descent parser in Aura for a tiny expression
language (`+ - * /`, parens, integers, identifiers, `let` bindings, `=`,
semicolons). Features:

- Hand-rolled lexer producing a token stream with `(peek)` lookahead
- Recursive descent with precedence climbing for `*`/`/`
- Error recovery via panic-mode synchronization at `;` and `EOF`
- AST construction with tagged-list nodes
- Pretty-printer that round-trips a parsed program back to source-ish text
- Pure unit tests over the lexer, parser and pretty-printer

Everything is in-memory: source text → tokens → AST → pretty text. No I/O
beyond `display`/`newline`.

---

## 1. Stdout contract (KEY=value lines, exact order)

The scenario prints exactly these 12 keys, one per line, in this order, then
exits. Values are computed from the actual parser/lexer output — no hardcoded
literals are substituted in `main.aura`.



A passing run MUST print all 12 lines in the listed order. A failing run
prints `FAIL=<reason>` instead and stops.

---

## 2. Module table

| File              | Required exported `define (api …)` forms                                                                                          |
|-------------------|----------------------------------------------------------------------------------------------------------------------------------|
| `token.aura`      | `(api make-token type lexeme line col)`, `(api token? v)`, `(api token-type t)`, `(api token-lexeme t)`, `(api token-line t)`, `(api token-col t)`, `(api token=? a b)`, `(api token-eof? t)` |
| `lexer.aura`      | `(api make-lexer src)`, `(api lexer-next lx)`, `(api lexer-peek lx)`, `(api lexer-eof? lx)`, `(api lexer-position lx)`           |
| `ast.aura`       | `(api make-num n)`, `(api make-var name)`, `(api make-binop op l r)`, `(api make-let name val body)`, `(api make-seq exprs)`, `(api ast? v)`, `(api ast-kind a)`, `(api ast-children a)`, `(api ast->list a)`, `(api ast-pretty a)` |
| `parser.aura`     | `(api parse-program toks)`, `(api parse-errors)`, `(api recovered-tokens)`                                                       |
| `precedence.aura` | `(api prec-of op)`, `(api is-left-assoc? op)`                                                                                    |
| `errors.aura`     | `(api make-error kind line col msg)`, `(api error? v)`, `(api error-kind e)`, `(api error-line e)`, `(api error-msg e)`          |
| `stream.aura`     | `(api stream-from-list xs)`, `(api stream-next s)`, `(api stream-peek s)`, `(api stream-eof? s)`                                 |
| `test-lex.aura`   | `(api test-lexer)`                                                                                                                |
| `test-parse.aura` | `(api test-parser)`, `(api test-errors)`                                                                                        |
| `main.aura`       | (driver; no `api` form required)                                                                                                 |

Loading order on the Aura CLI: `token.aura errors.aura stream.aura lexer.aura
ast.aura precedence.aura parser.aura test-lex.aura test-parse.aura main.aura`.

---

## 3. Public API contracts (per module)

### `token.aura`
A token is a tagged list `(token TYPE LEXEME LINE COL)` where `TYPE` is one of
`'num`, `'id`, `'+`, `'-`, `'*`, `'/'`, `'('`, `')'`, `'let`, `';'`, `'=`,
`'eof`. Exposes constructors, accessors, predicates, equality on `(type
lexeme)`, and `token-eof?`.

### `lexer.aura`
Owns an internal cursor `(stream-of-chars, line, col)`. `lexer-next` advances
and returns the next token (skipping whitespace, recognizing integers and
identifiers). `lexer-peek` returns the next token without consuming.
`lexer-eof?` checks whether the next token is `'eof`.

### `ast.aura`
AST nodes are tagged lists:
- `(num N)`, `(var NAME)`, `(binop OP LEFT RIGHT)`, `(let NAME VAL BODY)`,
  `(seq EXPRS)`.
`ast-children` returns the subnode list; `ast-pretty` renders the AST back to
source text using precedence-aware parenthesization.

### `parser.aura`
Implements the grammar:

Errors are collected (not thrown). On a bad token the parser enters panic mode,
records an `(error 'unexpected-token line col msg)`, then synchronizes by
discarding tokens until the next `';'` or `'eof'`. `parse-errors` returns the
collected errors, `recovered-tokens` returns the count of tokens consumed
during synchronization.

### `precedence.aura`
- `prec-of`: `'+'/'-'` → 1, `'*'/'/'` → 2, else → 0.
- `is-left-assoc?`: always `#t` for the supported binary ops.

### `errors.aura`
Tagged list `(error KIND LINE COL MSG)`. Predicates and accessors.

### `stream.aura`
Tiny list-backed peek/next stream used internally; also exposed for tests.

### `test-lex.aura`
`test-lexer` lexes `"let x = 10; x + 2 * (3 - 1)"`, returns token count
(expected 16 including EOF) and `#t` if the last token is `'eof`.

### `test-parse.aura`
- `test-parser` parses `"let x = 10; x + 2 * (3 - 1)"`, returns `#t` and the
  AST node count (expected 17 with a `(seq …)` root).
- `test-errors` parses `"let = 5; x + ; y"` and returns `(list ERR_COUNT
  ERR_KIND ERR_LINE)` = `(1 unexpected-token 1)`.

### `main.aura`
Calls `test-lexer`, `test-parser`, `test-errors`; then lexes a slightly
different program (`"let x = 10;\nfoo bar;\ny = 1 + 2"`), parses it, counts
AST nodes, pretty-prints it, pretty-prints the round-trip again, and checks
stability. Emits the 12 KEY=value lines from §1.

---

## 4. Scenario steps (main.aura)

1. `(set! lex-res (test-lexer))` — lex a clean expression.
2. `(set! parse-res (test-parser))` — parse a clean expression.
3. `(set! err-res (test-errors))` — confirm error path on broken input.
4. `(set! toks (lex-source "let x = 10;\nfoo bar;\ny = 1 + 2"))` — lex the
   scenario program.
5. `(set! ast (parse-program toks))` — parse it.
6. `(set! pretty1 (ast-pretty ast))` — first pretty-print.
7. `(set! pretty2 (ast-pretty (parse-program (lex-source pretty1))))` —
   round-trip.
8. `(set! stable (string=? pretty1 pretty2))` — check stability.
9. `display` the 12 keys in order, sourcing values from the above.

If any precondition fails, `main.aura` prints `FAIL=<reason>` and stops before
reaching the contract lines.

---

## 5. Anti-hardcode

`main.aura` derives every printed value from API calls:
- `LEX_TOKENS`, `LEX_EOF_OK` ← `test-lexer` return values.
- `PARSE_OK`, `PARSE_NODES` ← `test-parser` return values.
- `PRETTY_LEN` ← `string-length` of `ast-pretty`.
- `ROUNDTRIP_STABLE` ← equality of two `ast-pretty` outputs.
- `ERR_COUNT`, `ERR_KIND`, `ERR_LINE` ← `test-errors` (and asserted to equal
  the documented expectations).
- `RECOVERED_TOKEN` ← `(recovered-tokens)` after the bad parse, then
  verified against the fresh lex cursor.
- `PRETTY_HEAD` and `ROUNDTRIP_HEAD` ← `(substring … 0 15)` of each pretty
  string.

No `display` of a literal "true" / "187" / "unexpected-token" without that
value having been produced by a module API on this run.

---

## 6. How to run



Expected exit: 0. Expected stdout: exactly the 12 KEY=value lines from §1, in
order.

---
