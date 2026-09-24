# mini-saga — 10-file aura-build dogfood project (magnitude jump)

A **mini** travel-ish saga (book → pay → ship) with **compensate** +
**idempotency**, split across **ten files** — an order-of-magnitude harder Soft
dogfood than mini-2pc (7-file 2PC).

Success = stdout prints exactly:

```
OK=committed
ST1=held/charged/sent
DUP=dup
ST1B=held/charged/sent
FAIL_PAY=aborted
ST2=cancelled/none/none
FAIL_SHIP=aborted
ST3=cancelled/refunded/none
COUNT=4
```

with idemp + journal + book/pay/ship participants + step helper + compensate +
saga orchestrator + query status, and `main.aura` calling those ops (not bare
hardcoded display lines). See `GOAL.md`.

## Why order-of-magnitude harder vs mini-2pc

| | mini-2pc | **mini-saga** |
|--|----------|---------------|
| Files | 7 | **10** |
| Domains | log + parts + vote + coord + recover | **idemp + journal + book + pay + ship + step + compensate + saga + query + main** |
| Coupling | prepare→vote→decide→WAL→commit/abort | **forward steps + reverse compensate + per-step idemp keys + journal commit/abort** |
| Failure modes | poison / deny-b / sticky commit | **pay fail → cancel; ship fail → refund+cancel; dup must not double-charge; sticky always-committed / no-comp / wrong COUNT** |
| State machine | idle→prepared→{committed\|aborted} ×2 | **book/pay/ship each none→active→compensed + idemp set + journal** |

## How multi-file actually runs

```bash
$AURA_BIN idemp.aura journal.aura book.aura pay.aura ship.aura step.aura compensate.aura saga.aura query.aura main.aura
```

`verify.sh` uses CLI multi-file — honest, not a host-concat fake for cold SSOT.

## Layout

| File | Role |
|------|------|
| `GOAL.md` | Success predicate + 10-file saga contract |
| `stub/*.aura` | Intentionally wrong starters |
| `verify.sh` | Structural + `$AURA_BIN idemp.aura … main.aura` |
| `dogfood.json` | `files` (10), `run_mode=cli_multi`, expect/source_res |

## Dogfood with aura-build

```bash
export AURA_BIN=/workspace/aura-grok/build_soft4048/aura   # Aura #4048 Soft Ready
aura-build llm-dogfood --project examples/projects/mini-saga \
  --prefer-session --fiber-explore 3 --worldlines 3 --max-rounds 24 \
  --out trajectories/mini_saga_dogfood.jsonl --json

# registry alias:
aura-build llm-dogfood --task saga --max-rounds 24 --worldlines 3 --prefer-session --json
./examples/projects/mini-saga/verify.sh examples/projects/mini-saga/stub  # expect fail
```
