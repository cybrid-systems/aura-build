# mini-queue — 4-file aura-build dogfood project

A **mini** lease/ack job queue split across **four files** (harder than
mini-cache). Success = stdout prints exactly:

```
ENQ=2
LEASE_A=j1
LEASE_B=j2
LEASE_MISS=miss
ACK_OK=1
NACK_STATUS=pending
AFTER_TICK=pending
DONE=1
COUNT=4
```

with `queue-init` / `queue-enqueue` in `buf.aura`, `queue-lease` /
`queue-tick` in `lease.aura`, `queue-ack` / `queue-nack` / `queue-status` in
`ops.aura`, and `main.aura` calling those ops (not bare hardcoded display
lines). See `GOAL.md`.

## Why harder than mini-cache

| | mini-cache | mini-queue |
|--|------------|------------|
| Files | 3 | **4** |
| Domains | store + get/tick | buffer + lease/tick + ack/nack/status |
| State | key→(val,expire) | pending FIFO + leased + done |
| Expiry | get returns miss | tick **moves** leased → pending |
| Extra ops | — | ack / nack / status / third-lease miss |

## How multi-file actually runs

```bash
$AURA_BIN buf.aura lease.aura ops.aura main.aura
```

`verify.sh` uses CLI multi-file — honest, not a host-concat fake.

## Layout

| File | Role |
|------|------|
| `GOAL.md` | Success predicate + 4-file contract + lease model |
| `stub/*.aura` | Intentionally wrong starters |
| `verify.sh` | Structural + `$AURA_BIN buf.aura lease.aura ops.aura main.aura` |
| `dogfood.json` | `files` (4), `run_mode=cli_multi`, expect/source_res |

## Dogfood with aura-build

```bash
export AURA_BIN=/workspace/aura-redis/.deps/aura/build/aura
aura-build llm-dogfood --project examples/projects/mini-queue \
  --fiber-explore 3 --explore-tools rule,llm,intent --prefer-session \
  --max-rounds 16 --worldlines 3 \
  --out trajectories/mini_queue_dogfood.jsonl --json

# registry alias:
aura-build llm-dogfood --task queue --max-rounds 16 --worldlines 3 --prefer-session --json

# Manual stub check (should fail):
./examples/projects/mini-queue/verify.sh examples/projects/mini-queue/stub
```
