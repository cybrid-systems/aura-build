# mini-stack — harder aura-build dogfood project

A **mini** mutable stack Aura program (harder than mini-kv). Success = stdout
prints exactly:

```
TOP=30
POP=30
TOP2=20
SIZE=2
EMPTY=0
```

with named helpers `(define (stack-push …))` / `(stack-pop)` / `(stack-top)` /
`(stack-size)` (not bare hardcoded display lines alone). Semantics: push 10,20,30
→ top 30; pop 30; top 20; size 2; empty 0.

## Layout

| File | Role |
|------|------|
| `GOAL.md` | Plain-language success predicate + exact stdout + structure |
| `stub.aura` | Intentionally wrong/incomplete starter |
| `verify.sh` | Structural + `$AURA_BIN` run; exit 0 iff TOP/POP/TOP2/SIZE/EMPTY green |
| `dogfood.json` | Machine contract for `llm-dogfood --project` |

## Dogfood with aura-build

```bash
export AURA_BIN=/workspace/aura-redis/.deps/aura/build/aura
# Preferred: load project dir (GOAL + stub + verify.sh / dogfood.json)
aura-build llm-dogfood --project examples/projects/mini-stack --max-rounds 10 \
  --worldlines 3 --out trajectories/mini_stack_dogfood.jsonl --json

# Or registry alias:
aura-build llm-dogfood --task stack --max-rounds 10 --worldlines 3 --json

# Manual stub check (should fail):
./examples/projects/mini-stack/verify.sh examples/projects/mini-stack/stub.aura
```

## Lessons

- Stack state machine needs four+ named helpers; verify checks substrings so
  hardcode-only displays fail even if stdout looks right.
- Prefer `--project` over baking every new tier into `--task` choices; optional
  `--task stack` is a thin registry alias that auto-loads this dir’s verify.sh.
- **Zero-arity defines:** `(define (stack-pop) …)` has `)` immediately after the
  name — verify/`source_res` must use ``, not a trailing `[[:space:]]`, or
  real stack helpers fail structural checks.
- **Repair context:** llm-dogfood now injects required `source_res` patterns into
  repair prompts and uses task-agnostic `matched_expect` (TOP=/POP=/… not just
  GET_/ADD=).

Honesty: never claim `fiber_live` / `incr_proven` unless prove/doctor measured them.
