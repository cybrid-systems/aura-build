# mini-router — 3-file aura-build dogfood project

A **mini** HTTP-ish router split across **three files** (harder than mini-bank).
Success = stdout prints exactly:

```
GET_SLASH=home
GET_API=api
GET_API_V1=api
GET_API_V2=api
POST_API=405
MISS=404
COUNT=5
```

with `route-register` in `table.aura`, `route-lookup` in `match.aura`, and
`main.aura` calling `route-lookup` (not bare hardcoded display lines alone).

`COUNT=5` = number of scenario lookups whose result is not `404` (the five
lines before `MISS`).

## How multi-file actually runs

```bash
$AURA_BIN table.aura match.aura main.aura
```

`verify.sh` uses CLI multi-file — honest, not a host-concat fake.

## Layout

| File | Role |
|------|------|
| `GOAL.md` | Success predicate + 3-file contract |
| `stub/table.aura`, `stub/match.aura`, `stub/main.aura` | Intentionally wrong starters |
| `verify.sh` | Structural + `$AURA_BIN table.aura match.aura main.aura` |
| `dogfood.json` | `files` (3), `run_mode=cli_multi`, expect/source_res |

## Dogfood with aura-build

```bash
export AURA_BIN=/workspace/aura-redis/.deps/aura/build/aura
aura-build llm-dogfood --project examples/projects/mini-router --max-rounds 12 \
  --worldlines 3 --out trajectories/mini_router_dogfood.jsonl --json

# registry alias:
aura-build llm-dogfood --task router --max-rounds 12 --worldlines 3 --json

# Manual stub check (should fail):
./examples/projects/mini-router/verify.sh examples/projects/mini-router/stub
```
