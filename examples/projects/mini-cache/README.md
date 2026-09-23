# mini-cache — 3-file aura-build dogfood project

A **mini** TTL string cache split across **three files** (harder than mini-router).
Success = stdout prints exactly:

```
GET_A=1
GET_MISS=miss
GET_B=2
TTL_EXPIRED=miss
COUNT=2
```

with `cache-init` / `cache-set` in `store.aura`, `cache-get` / `cache-tick` in
`ops.aura`, and `main.aura` calling those ops (not bare hardcoded display lines).

Tick model: global `tick`; `cache-set` stores `(val . expire-tick)` with
expire-tick = `#f` when ttl=0 else `tick+ttl`; `cache-tick n` advances tick;
expired keys return `"miss"`. See `GOAL.md`.

## How multi-file actually runs

```bash
$AURA_BIN store.aura ops.aura main.aura
```

`verify.sh` uses CLI multi-file — honest, not a host-concat fake.

## Layout

| File | Role |
|------|------|
| `GOAL.md` | Success predicate + 3-file contract + tick model |
| `stub/store.aura`, `stub/ops.aura`, `stub/main.aura` | Intentionally wrong starters |
| `verify.sh` | Structural + `$AURA_BIN store.aura ops.aura main.aura` |
| `dogfood.json` | `files` (3), `run_mode=cli_multi`, expect/source_res |

## Dogfood with aura-build

```bash
export AURA_BIN=/workspace/aura-redis/.deps/aura/build/aura
aura-build llm-dogfood --project examples/projects/mini-cache --max-rounds 12 \
  --worldlines 3 --prefer-session --out trajectories/mini_cache_dogfood.jsonl --json

# registry alias:
aura-build llm-dogfood --task cache --max-rounds 12 --worldlines 3 --prefer-session --json

# Manual stub check (should fail):
./examples/projects/mini-cache/verify.sh examples/projects/mini-cache/stub
```
