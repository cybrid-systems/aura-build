# Packrat PEG Parser Combinator — mini-peg-packrat

## Overview

A small in-memory **Parsing Expression Grammar (PEG)** framework implemented in Aura Lisp, using **packrat-style memoization** for linear-time parsing, **left-recursion detection** via the seed/recall algorithm, **semantic actions** (user-supplied functions wrapped over parse results), and a **combinator API** (`seq`, `alt`, `star`, `plus`, `opt`, `token`, `satisfies`, `between`, `sep-by`). A small **INI-style config** grammar is included as a worked example and is parsed to produce a nested alist of sections/keys.

The "input program" is a sample INI source string. The system parses it through the full PEG pipeline (lexer-free, char-level), detects any left-recursive rules at definition time, and prints the resulting alist plus a small statistics summary.

---

## Stdout Contract

The scenario MUST print the following 12 lines, in this exact order, with `KEY=value` form (one per line, terminated by `(newline)`). Values are illustrative shapes; the harness measures them from a Python reference.



`SEM_DB_HOST` / `SEM_DB_PORT` / `SEM_APP_NAME` come from the parsed INI so their values must be derived from the parsed alist via the module API (not hardcoded literals).

---

## Module / File Table

| File | Required `define (api …)` forms |
|------|---------------------------------|
| `aura/prelude.aura` | `(api length)`, `(api nth)`, `(api take)`, `(api drop)`, `(api reverse*)`, `(api append*)` |
| `aura/source.aura` | `(api source-new)`, `(api source-pos)`, `(api source-eof?)`, `(api source-peek)`, `(api source-rest)`, `(api source-slice)`, `(api source-len)` |
| `aura/peg/result.aura` | `(api mk-ok)`, `(api mk-fail)`, `(api res-ok?)`, `(api res-value)`, `(api res-rest)`, `(api res-cons)` |
| `aura/peg/memo.aura` | `(api memo-new)`, `(api memo-get)`, `(api memo-put)`, `(api memo-hits)`, `(api memo-misses)` |
| `aura/peg/combinator.aura` | `(api peg-seq)`, `(api peg-alt)`, `(api peg-star)`, `(api peg-plus)`, `(api peg-opt)`, `(api peg-token)`, `(api peg-any)`, `(api peg-satisfies)`, `(api peg-between)`, `(api peg-sep-by)`, `(api peg-action)` |
| `aura/peg/builder.aura` | `(api rule-new)`, `(api rule-name)`, `(api rule-body)`, `(api rule-action)`, `(api rule-lrec?)`, `(api rule-mark-lrec)`, `(api grammar-new)`, `(api grammar-add!)`, `(api grammar-get)`, `(api grammar-names)`, `(api grammar-check-lrec!)` |
| `aura/peg/parser.aura` | `(api parse-rule)`, `(api parse-grammar)`, `(api stats-nodes)` |
| `aura/grammars/ini-lexer.aura` | `(api ini-tokenize)` — char-level splitter for INI (lines/comments/blank) |
| `aura/grammars/ini-rules.aura` | `(api ini-build-grammar)`, `(api ini-section?)`, `(api ini-key?)`, `(api ini-value?)` |
| `aura/grammars/ini-semantic.aura` | `(api ini-semantic)`, `(api ini-section-action)`, `(api ini-key-action)` |
| `aura/grammars/ini-run.aura` | `(api ini-parse)`, `(api ini-get)`, `(api ini-sections)`, `(api ini-flat-keys)` |
| `aura/util/assert.aura` | `(api assert)`, `(api assert-eq)` |
| `main.aura` | driver — calls APIs, prints the 12 KEY=… lines |

13 `.aura` files total; `main.aura` is last.

---

## Scenario Steps (executed in `main.aura`)

1. Load the prelude utilities via `(load "aura/prelude.aura") …`.
2. Construct the INI source string via `source-new` with a fixed sample:
   
3. Build the INI grammar by calling `(ini-build-grammar)`; assert it returns a grammar with rules named `ini`, `section`, `key`, `value`, `ws`, `ident`.
4. Call `(grammar-check-lrec!)` on the grammar; expect `LEFT_RECURSIVE=none`.
5. Call `(ini-parse source grammar)`; bind the returned alist.
6. Walk the alist using `(ini-sections)` and `(ini-flat-keys)`; pull specific keys with `(ini-get 'db 'host)` etc.
7. Print all 12 KEY=value lines derived from API outputs (length of source = `INPUT_BYTES`, memo stats from `(memo-hits)`/`(memo-misses)`, node count from `(stats-nodes)`, semantic values from the alist).

---

## Anti-Hardcode

`main.aura` must NOT just `display` hardcoded strings. It must:

- obtain `INPUT_BYTES` by calling `(source-len s)`,
- obtain `MEMO_HITS` / `MEMO_MISSES` by calling `(memo-hits m)` and `(memo-misses m)` on the memo table returned by the parser,
- obtain `OK_SECTIONS` / `OK_KEYS` by `(length (ini-sections alist))` / `(length (ini-flat-keys alist))`,
- obtain `SEM_DB_HOST` / `SEM_DB_PORT` / `SEM_APP_NAME` by `(ini-get 'db 'host)` style lookups on the parsed alist,
- obtain `LEFT_RECURSIVE=none` by checking `(grammar-check-lrec!)` returned `'none`.

If any of these are string literals rather than API results, the run fails validation.

---

## How to Run



All files share one top-level environment. The CLI loads them left-to-right; `main.aura` performs the scenario and prints the 12-line stdout contract.

---
