# mini-calc — slightly harder aura-build dogfood project

A **mini** Aura program trial (harder than mini-greet). Success = stdout prints
exactly:

```
ADD=7
MUL=12
MIX=17
```

with named helpers `(define (add …))` / `(define (mul …))` (not bare hardcoded
display lines alone). Semantics: ADD=3+4, MUL=3*4, MIX=(3*4)+5.

## Layout

| File | Role |
|------|------|
| `GOAL.md` | Plain-language success predicate + exact stdout + structure |
| `stub.aura` | Intentionally wrong/incomplete starter |
| `verify.sh` | Structural + `$AURA_BIN` run; exit 0 iff ADD/MUL/MIX green |

## Dogfood with aura-build

```bash
export AURA_BIN=/workspace/aura-redis/.deps/aura/build/aura
# Closed loop: MiniMax proposes → Aura verifies → repair worldlines
aura-build llm-dogfood --task calc --max-rounds 8 --worldlines 3 \
  --out trajectories/mini_calc_dogfood.jsonl --json

# Manual stub check (should fail):
./examples/projects/mini-calc/verify.sh examples/projects/mini-calc/stub.aura
```

Also smoke pursue against the goal text (orch-native fitness; MiniMax never
controls the loop):

```bash
aura-build pursue --goal "Aura calc: print ADD=7 MUL=12 MIX=17 via define add/mul" \
  --max-rounds 2 --worldlines 2 --json
```

Honesty: never claim `fiber_live` / `incr_proven` unless prove/doctor measured them.
