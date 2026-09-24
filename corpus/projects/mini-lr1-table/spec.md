```markdown
# mini-lr1-table — LALR(1) Table Builder & Parser

## Overview

A toy LALR(1) parser-construction pipeline written in pure Aura. Twelve `.aura`
files cooperate to:

1. Load a small grammar (productions, terminals, non-terminals, start symbol).
2. Build LR(1) item sets and the LR(1) DFA.
3. **Fold** the LR(1) states into LALR(1) by merging states with identical LR(0)
   cores (a `core-eq?` helper drives this).
4. Build `ACTION` / `GOTO` tables, detect shift/reduce and reduce/reduce
   conflicts, and emit a *heuristic* resolution (prefer shift, prefer earlier
   production) so the table is always populated for a toy grammar.
5. Drive a generic LALR(1) parser: tokenize, run the state machine, emit an AST,
   and recover from syntax errors using a tiny *set-based follow reduction*
   (panic-mode over a fixed follow set per non-terminal).

`main.aura` exercises everything: it builds tables for two grammars (one
expression, one ambiguous), parses three inputs (clean, recoverable error,
multi-error), then prints a fixed stdout contract.

No I/O besides `display`/`newline`. No Python. No external dependencies.

---

## Stdout Contract (exact order)

The program prints exactly these lines, in order, with no blank lines:



`RESULT=ok` is printed last. All numeric values come from real parser
computations — not literals hard-coded in `main.aura`.

---

## Module Table

| File | Required exported `(define (api …))` forms |
|---|---|
| `grammar.aura` | `(api grammar-make)`, `(api grammar-add-prod)`, `(api grammar-symbols)`, `(api grammar-start)`, `(api grammar-productions-of)`, `(api grammar-terminals)`, `(api grammar-nonterminals)` |
| `item.aura` | `(api item-make)`, `(api item-core)`, `(api item-dot)`, `(api item-lookahead)`, `(api item-eq?)`, `(api item-closure)` |
| `lr1-states.aura` | `(api lr1-build-states)`, `(api lr1-state-items)`, `(api lr1-state-id)`, `(api lr1-goto)` |
| `lalr-fold.aura` | `(api lalr-fold)`, `(api core-eq?)`, `(api lalr-state-items)`, `(api lalr-state-id)` |
| `tables.aura` | `(api tables-build)`, `(api tables-action)`, `(api tables-goto)`, `(api tables-conflicts)` |
| `lexer.aura` | `(api lex)`, `(api token-kind)`, `(api token-text)` |
| `parser.aura` | `(api parser-run)`, `(api ast-root)`, `(api ast-children)`, `(api parser-shifts)`, `(api parser-reduces)`, `(api parser-tokens-consumed)`, `(api parser-error?)` |
| `error-recovery.aura` | `(api recovery-init)`, `(api recovery-attempt)`, `(api recovery-follow-reductions)` |
| `follow.aura` | `(api follow-compute)`, `(api follow-of)` |
| `ast.aura` | `(api ast-make)`, `(api ast-add-child)`, `(api ast-count)` |
| `conflict.aura` | `(api conflict-record)`, `(api conflict-count-shift-reduce)`, `(api conflict-count-reduce-reduce)` |
| `main.aura` | (entry point — orchestrates and prints) |

---

## Scenario Steps (`main.aura` only)

`main.aura` performs, in order:

1. **Build Grammar A** (unambiguous expression grammar):
   `E → E + T | T`, `T → T * F | F`, `F → ( E ) | id`.
   Call `grammar-make`, then `grammar-add-prod` for each production.
2. **Build Grammar B** (intentionally ambiguous: dangling else not modelled,
   but uses `S → S S | a` so it has a known shift/reduce conflict after folding).
   Same API calls.
3. **Compute LR(1) states** for Grammar A via `lr1-build-states`. Count states.
4. **Fold to LALR(1)** via `lalr-fold`. Count states; assert fewer than LR(1).
5. **Build ACTION/GOTO tables** via `tables-build` for both grammars. Pull
   `(api tables-conflicts)` and feed into `conflict-record` to produce the
   `CONFLICTS_*` keys.
6. **Compute follow sets** for Grammar A via `follow-compute`.
7. **Lex** three input strings:
   - `"id + id * id"`        (clean parse)
   - `"id + + * id"`         (error → recovery)
   - `"id id id + id"`       (multi-error)
   via `lex`. Count tokens per stream to feed `TOKENS_CONSUMED`.
8. **Parse** the clean input via `parser-run` using LALR(1) table for Grammar A.
   Verify `parser-error?` is `#f`. Count `parser-shifts`, `parser-reduces`,
   `parser-tokens-consumed`. Walk AST with `ast-root`/`ast-children` and call
   `ast-count` for `AST_NODES_CLEAN`.
9. **Parse** the error input. Initialize `recovery-init`, call
   `recovery-attempt` on the error result, then re-feed the recovered token
   stream. Verify `parser-error?` ends `#f`. Count nodes (some subtrees are
   dropped, hence `AST_NODES_RECOVERED < AST_NODES_CLEAN`). Track
   `recovery-follow-reductions` for the `FOLLOW_REDUCTIONS` key.
10. **Count `parser-shifts`/`parser-reduces` summed across both parses** for
    the `SHIFTS` / `REDUCES` keys. Count distinct `(state, nonterm)` `GOTO`
    entries in the table for `GOTOS`.
11. **Print** the 15 `KEY=value` lines in the exact order above. End with
    `RESULT=ok`.

---

## Anti-Hardcode Notes

`main.aura` may not embed any of the literal numeric values shown in the
stdout contract. Every key must be derived from calls into the module APIs:

- `LR1_STATES`, `LALR1_STATES` ← `(length (lr1-build-states …))` and the
  folded list length.
- `CONFLICTS_*` ← counters returned by `conflict-count-*`.
- `AST_NODES_*` ← `(ast-count …)` over the produced AST.
- `SHIFTS`, `REDUCES`, `TOKENS_CONSUMED`, `FOLLOW_REDUCTIONS`,
  `GOTOS` ← all returned by parser / recovery / table APIs.

A solution that displays the expected strings without invoking these APIs will
fail verification, because the reference Python harness re-runs the Aura
program and checks each value against the freshly-computed number.

---

## How to Run

```sh
aura grammar.aura item.aura lr1-states.aura lalr-fold.aura tables.aura \
     lexer.aura parser.aura error-recovery.aura follow.aura ast.aura \
     conflict.aura main.aura
json
{
  "files": [
    "grammar.aura",
    "item.aura",
    "lr1-states.aura",
    "lalr-fold.aura",
    "tables.aura",
    "lexer.aura",
    "parser.aura",
    "error-recovery.aura",
    "follow.aura",
    "ast.aura",
    "conflict.aura",
    "main.aura"
  ],
  "entry": "main.aura",
  "run_mode": "cli_multi",
  "expect_keys": [
    "LR1_STATES",
    "LALR1_STATES",
    "GRAMMARS_LOADED",
    "CONFLICTS_SHIFT_REDUCE",
    "CONFLICTS_REDUCE_REDUCE",
    "PARSED_CLEAN_OK",
    "PARSED_ERROR_RECOVERED",
    "AST_NODES_CLEAN",
    "AST_NODES_RECOVERED",
    "TOKENS_CONSUMED",
    "FOLLOW_REDUCTIONS",
    "SHIFTS",
    "REDUCES",
    "GOTOS",
    "RESULT"
  ],
  "source_res": [
    "\\(define\\s+\\(grammar-make\\b",
    "\\(define\\s+\\(grammar-add-prod\\b",
    "\\(define\\s+\\(grammar-symbols\\b",
    "\\(define\\s+\\(grammar-start\\b",
    "\\(define\\s+\\(grammar-productions-of\\b",
    "\\(define\\s+\\(grammar-terminals\\b",
    "\\(define\\s+\\(grammar-nonterminals\\b",
    "\\(define\\s+\\(item-make\\b",
    "\\(define\\s+\\(item-core\\b",
    "\\(define\\s+\\(item-dot\\b",
    "\\(define\\s+\\(item-lookahead\\b",
    "\\(define\\s+\\(item-eq\\?\\b",
    "\\(define\\s+\\(item-closure\\b",
    "\\(define\\s+\\(lr1-build-states\\b",
    "\\(define\\s+\\(lr1-state-items\\b",
    "\\(define\\s+\\(lr1-state-id\\b",
    "\\(define\\s+\\(lr1-goto\\b",
    "\\(define\\s+\\(lalr-fold\\b",
    "\\(define\\s+\\(core-eq\\?\\b",
    "\\(define\\s+\\(lalr-state-items\\b",
    "\\(define\\s+\\(lalr-state-id\\b",
    "\\(define\\s+\\(tables-build\\b",
    "\\(define\\s+\\(tables-action\\b",
    "\\(define\\s+\\(tables-goto\\b",
    "\\(define\\s+\\(tables-conflicts\\b",
    "\\(define\\s+\\(lex\\b",
    "\\(define\\s+\\(token-kind\\b",
    "\\(define\\s+\\(token-text\\b",
    "\\(define\\s+\\(parser-run\\b",
    "\\(define\\s+\\(ast-root\\b",
    "\\(define\\s+\\(ast-children\\b",
    "\\(define\\s+\\(parser-shifts\\b",
    "\\(define\\s+\\(parser-reduces\\b",
    "\\(define\\s+\\(parser-tokens-consumed\\b",
    "\\(define\\s+\\(parser-error\\?\\b",
    "\\(define\\s+\\(recovery-init\\b",
    "\\(define\\s+\\(recovery-attempt\\b",
    "\\(define\\s+\\(recovery-follow-reductions\\b",
    "\\(define\\s+\\(follow-compute\\b",
    "\\(define\\s+\\(follow-of\\b",
    "\\(define\\s+\\(ast-make\\b",
    "\\(define\\s+\\(ast-add-child\\b",
    "\\(define\\s+\\(ast-count\\b",
    "\\(define\\s+\\(conflict-record\\b",
    "\\(define\\s+\\(conflict-count-shift-reduce\\b",
    "\\(define\\s+\\(conflict-count-reduce-reduce\\b"
  ]
}
```
