# mini-bank — multi-file aura-build dogfood project

A **mini** bank/transfer Aura program split across **two files** (harder than
mini-stack). Success = stdout prints exactly:

```
A=100
B=50
A2=70
B2=80
OK=1
```

with `(define (credit …))` / `(debit …)` / `(balance …)` in `lib.aura`, called
from `main.aura` (not bare hardcoded display lines in main alone).

## How multi-file actually runs

Aura binary accepts multiple files natively:

```bash
$AURA_BIN lib.aura main.aura
```

`(load "lib.aura")` also works. `verify.sh` uses CLI multi-file — honest, not a
host-concat fake of native modules.

## Layout

| File | Role |
|------|------|
| `GOAL.md` | Success predicate + multi-file contract |
| `stub/lib.aura`, `stub/main.aura` | Intentionally wrong starters |
| `verify.sh` | Structural + `$AURA_BIN lib.aura main.aura` |
| `dogfood.json` | `files`, `run_mode=cli_multi`, expect/source_res |

## Dogfood with aura-build

```bash
export AURA_BIN=/workspace/aura-redis/.deps/aura/build/aura
aura-build llm-dogfood --project examples/projects/mini-bank --max-rounds 12 \
  --worldlines 3 --out trajectories/mini_bank_dogfood.jsonl --json

# Manual stub check (should fail):
./examples/projects/mini-bank/verify.sh examples/projects/mini-bank/stub
```
