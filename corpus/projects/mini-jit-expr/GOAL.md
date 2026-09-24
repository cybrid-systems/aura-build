# GOAL.md — mini-jit-expr

## Overview
A toy **JIT expression compiler** written in pure Aura (Lisp-like). The system ingests a small typed arithmetic/predicate grammar, performs AST → typed-IR → stack-IR lowering, then "emits" machine code via a portable textual codegen backend (one of three selectable targets: `x86`, `arm64`, `wasm`). A constant-folder pass reduces obvious arithmetic identities before lowering. The "JIT" does not require any external toolchain: codegen output is a textual assembly-like listing that the harness displays, plus a simulated exec via a tiny stack interpreter that runs the lowered IR to verify functional equivalence against the typed interpreter. The whole thing is in-memory; no files are read or written beyond stdout.

## Stdout contract — exact `KEY=value` lines (in order)



(10 keys, one per line, in this exact order, exact casing.)

## Module table

| File | Required exported `(api …)` forms |
|------|-----------------------------------|
| `01_lexer.aura` | `(api lex-expr (src) → tokens)`, `(api token-kind? (tok k) → bool)` |
| `02_parser.aura` | `(api parse-expr (tokens) → ast)`, `(api ast-node-kind (node) → sym)`, `(api ast-children (node) → list)` |
| `03_ast.aura` | `(api mk-num (n) → node)`, `(api mk-var (name) → node)`, `(api mk-binop (op l r) → node)`, `(api mk-pred (op l r) → node)` |
| `04_typecheck.aura` | `(api type-check (ast env) → typed-ast)`, `(api type-of (typed-ast) → sym)` |
| `05_env.aura` | `(api env-empty () → env)`, `(api env-bind (env k v) → env)`, `(api env-lookup (env k) → val)` |
| `06_constfold.aura` | `(api const-fold (typed-ast) → typed-ast)`, `(api fold-hits () → n)` |
| `07_ir.aura` | `(api ir-build (typed-ast) → ir)`, `(api ir-len (ir) → n)`, `(api ir-instr (ir i) → instr)` |
| `08_lower.aura` | `(api lower-to-stack-ir (ir) → sir)`, `(api sir-len (sir) → n)` |
| `09_codegen.aura` | `(api codegen (sir target) → text)`, `(api codegen-byte-count (text) → n)`, `(api codegen-target () → sym)` |
| `10_targets.aura` | `(api target-set (name) → bool)`, `(api target-name () → sym)`, `(api target-emit-prologue (tgt) → text)`, `(api target-emit-epilogue (tgt) → text)` |
| `11_backend_x86.aura` | `(api x86-emit (sir) → text)`, `(api x86-label (n) → text)` |
| `12_backend_arm64.aura` | `(api arm64-emit (sir) → text)`, `(api arm64-label (n) → text)` |
| `13_backend_wasm.aura` | `(api wasm-emit (sir) → text)`, `(api wasm-label (n) → text)` |
| `14_exec.aura` | `(api exec-ir (sir env) → val)`, `(api exec-ok? (sir env expected) → bool)` |
| `main.aura` | orchestrates lexer→parser→typecheck→constfold→ir→lower→codegen→exec, prints the 10 keys |

## Scenario steps executed in `main.aura`

1. `(target-set "x86")` → chooses backend; record `(codegen-target)` returns `'x86`.
2. Call `(lex-expr src)` with a fixed expression like `"(x + 3) * (y > 0)"`; verify every token has a recognized `(token-kind? tok 'num-or-id-or-punct)` shape; set `FRONTEND_PARSE_OK=1`.
3. `(parse-expr tokens)` to AST; traverse AST with `(ast-children n)` and count nodes; record `FRONTEND_AST_NODES=5` (num, var, binop, var, pred).
4. Build env binding `x=4, y=7`; `(type-check ast env)`; on success `TYPE_CHECK_OK=1`.
5. `(const-fold typed-ast)`; read `(fold-hits)`; record `CONST_FOLD_HITS=2` (e.g. `3 + 0` and `1 * x` folds).
6. `(ir-build folded)` then `(ir-len ir)` → `IR_INSTRUCTIONS=11`.
7. `(lower-to-stack-ir ir)` then `(sir-len sir)` (used implicitly).
8. `(codegen sir (codegen-target))` → text; `(codegen-byte-count text)` → `CODEGEN_BYTES=42`.
9. `(exec-ir sir env)` with same env → `EXEC_RESULT=14` (i.e. `(4+3) * (7>0) = 7 * 1 = 7`? or another canonical fixture yielding `14`); `(exec-ok? sir env 14)` → `EXEC_OK=1`.
10. Wrap steps 1–9 in a timer; emit `DRIVER_MS=<elapsed>`.
11. Print all 10 `KEY=value` lines in order.

The expression and env are chosen so that `EXEC_RESULT=14` is *computed* by the stack interpreter, not hardcoded.

## Anti-hardcode

`main.aura` MUST:
- Call `parse-expr`, `type-check`, `const-fold`, `ir-build`, `lower-to-stack-ir`, `codegen`, and `exec-ir` to compute every numeric value before printing.
- The literal `14` only appears as the expected-value argument to `exec-ok?`, never as the printed `EXEC_RESULT=`.
- `FRONTEND_AST_NODES`, `CONST_FOLD_HITS`, `IR_INSTRUCTIONS`, `CODEGEN_BYTES` are obtained from API calls (counts returned by the modules), not embedded constants.
- `EXEC_RESULT` is the value returned by `(exec-ir …)`.
- A reviewer can change the expression string and env to see all derived keys shift accordingly while `EXEC_OK=1` is recomputed.

## How to run



Expected stdout (order matters, exact strings):
