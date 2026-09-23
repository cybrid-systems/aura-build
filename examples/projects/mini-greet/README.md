# mini-greet — tiny aura-build dogfood project

A **mini** Aura program trial (not aura-redis). Success = stdout contains
`GREET=aura` exactly as a token.

## Layout

| File | Role |
|------|------|
| `GOAL.md` | Plain-language success predicate + exact stdout |
| `stub.aura` | Intentionally wrong starter (`GREET=wrong`) |
| `verify.sh` | Runs `$AURA_BIN` on a candidate; exit 0 iff `GREET=aura` |

## Dogfood with aura-build

```bash
export AURA_BIN=/workspace/aura-redis/.deps/aura/build/aura
# Closed loop: MiniMax proposes → Aura verifies → repair worldlines
aura-build llm-dogfood --task greet --max-rounds 8 --worldlines 3 --json

# Manual stub check (should fail):
./examples/projects/mini-greet/verify.sh examples/projects/mini-greet/stub.aura
```

Also smoke pursue against the goal text (orch-native fitness; MiniMax never
controls the loop):

```bash
aura-build pursue --goal "print GREET=aura" --max-rounds 2 --worldlines 2 --json
```

## Self-evolve (next step — after this dogfood is green)

aura-build can **self-evolve** its own product code once external mini
projects like this verify green:

```bash
# Dry only (no push). Prefer --no-commit until changes are clearly useful.
aura-build self-evolve --prompt "dry after mini-greet" --no-push --verify smoke
```

Do **not** push self-evolve commits unless verify is green and the diff is
product-useful. This README documents the path; the primary ask is the
mini-greet dogfood itself.

Honesty: never claim `fiber_live` / `incr_proven` unless prove/doctor measured them.
