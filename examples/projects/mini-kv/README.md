# mini-kv — harder aura-build dogfood project

A **mini** in-memory key/value Aura program (harder than mini-calc). Success =
stdout prints exactly:

```
GET_a=1
GET_b=2
MISS=nil
GET_c=3
```

with named helpers `(define (kv-set …))` / `(define (kv-get …))` (not bare
hardcoded display lines alone). Semantics: set a→1, set b→2, get a/b, miss→nil,
set c→3, get c.

## Layout

| File | Role |
|------|------|
| `GOAL.md` | Plain-language success predicate + exact stdout + structure |
| `stub.aura` | Intentionally wrong/incomplete starter |
| `verify.sh` | Structural + `$AURA_BIN` run; exit 0 iff GET_*/MISS green |
| `dogfood.json` | Machine contract for `llm-dogfood --project` |

## Dogfood with aura-build

```bash
export AURA_BIN=/workspace/aura-redis/.deps/aura/build/aura
# Preferred: load project dir (GOAL + stub + verify.sh / dogfood.json)
aura-build llm-dogfood --project examples/projects/mini-kv --max-rounds 8 \
  --worldlines 3 --out trajectories/mini_kv_dogfood.jsonl --json

# Or registry alias:
aura-build llm-dogfood --task kv --max-rounds 8 --worldlines 3 --json

# Manual stub check (should fail):
./examples/projects/mini-kv/verify.sh examples/projects/mini-kv/stub.aura
```

Honesty: never claim `fiber_live` / `incr_proven` unless prove/doctor measured them.
