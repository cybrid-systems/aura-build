# GOAL.md — mini-pratt-expr

A small in-memory Pratt (top-down operator precedence) parser for a SQL-like expression grammar. The pipeline tokenizes input, parses into a tagged AST (binary ops, unary ops, function calls, NULL, literals, case-when), and exposes a tree-walking evaluator that returns a typed result. The scenario feeds three expressions through the full pipeline and prints structured `KEY=value` lines summarizing tokens, AST shape, and evaluated values.

## Stdout contract (exact order)



## Module table

| File | Required exported `define` forms |
|------|----------------------------------|
| `token.aura` | `(define (api-tokenize src) -> list-of-tokens)`, `(define (api-token-type t) -> sym)`, `(define (api-token-value t) -> string)` |
| `ast.aura` | `(define (api-make-num n))`, `(define (api-make-str s))`, `(define (api-make-null))`, `(define (api-make-bool b))`, `(define (api-make-var name))`, `(define (api-make-bin op l r))`, `(define (api-make-un op e))`, `(define (api-make-call name args))`, `(define (api-make-case whens otherwise))`, `(define (api-make-when cond then))`, `(define (api-ast? x))` |
| `pratt.aura` | `(define (api-parse tokens env) -> ast)`, `(define (api-prefix-power sym))`, `(define (api-infix-power sym))` |
| `env.aura` | `(define (api-env-empty))`, `(define (api-env-set env k v))`, `(define (api-env-get env k) -> value-or-false)` |
| `eval.aura` | `(define (api-eval ast env) -> typed-value)`, `(define (api-type-of v) -> sym)`, `(define (api-bool-of v))`, `(define (api-num-of v))` |
| `binop.aura` | `(define (api-apply-bin op a b) -> typed-value)` |
| `unop.aura` | `(define (api-apply-un op a) -> typed-value)` |
| `call.aura` | `(define (api-apply-call name args env) -> typed-value)` |
| `main.aura` | driver: loads samples, tokenizes, parses, evaluates, prints contract |

## Scenario steps (main.aura)

1. Build a sample list `'( "1 + 2 * 3" "-NOT NULL AND (x = NULL)" "CASE WHEN x > 0 THEN x ELSE -x END")`.
2. Build environment with `x = 3`.
3. For each sample (indexed `i`):
   - Call `(api-tokenize expr)` → tokens list.
   - Call `(api-parse tokens env)` → AST node.
   - Count nodes via a small recursive `count-nodes` walker.
   - Call `(api-eval ast env)` → typed value.
   - Print `EXPR[i]`, `TOKENS[i]=<len>`, `NODES[i]=<count>`, `EVAL[i]=<type> <repr>`.
4. Print `SAMPLES=3` and `RESULT=PASS` if all three evaluate without error.

## Anti-hardcode

`main.aura` must invoke `api-tokenize`, `api-parse`, and `api-eval` for every sample. The numbers printed (`TOKENS[i]`, `NODES[i]`, `EVAL[i]` values) are derived from the actual AST traversal and evaluator outputs — not hardcoded literals. Changing any operator precedence or `x` env value will alter `EVAL` outputs naturally.

## How to run



Each file is loaded in order on a single Aura CLI invocation, sharing the top-level environment.
