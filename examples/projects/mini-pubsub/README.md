# mini-pubsub — 5-file aura-build dogfood project

A **mini** pub/sub bus split across **five files** (harder than mini-queue).
Success = stdout prints exactly:

```
SUBS=2
PUB=2
POLL_A=hello
POLL_B=hello
POLL_MISS=miss
AFTER_UNSUB=1
POLL_A2=miss
POLL_B2=world
COUNT=3
```

with `bus-init` / `topic-create` in `topic.aura`, `subscribe` /
`unsubscribe` / `sub-list` in `sub.aura`, `publish` in `pub.aura`,
`poll` / `pending-count` in `deliver.aura`, and `main.aura` calling those
ops (not bare hardcoded display lines). See `GOAL.md`.

## Why harder than mini-queue

| | mini-queue | mini-pubsub |
|--|------------|-------------|
| Files | 4 | **5** |
| Domains | buf + lease/tick + ack/nack | topic + sub + pub + deliver + main |
| State | pending/leased/done | topics → subs + per-sub mailboxes |
| Coupling | lease expires via tick | **fan-out** publish + **unsubscribe** changes later delivery |
| Extra ops | ack / nack / status | subscribe / unsubscribe / poll / pending-count |

## How multi-file actually runs

```bash
$AURA_BIN topic.aura sub.aura pub.aura deliver.aura main.aura
```

`verify.sh` uses CLI multi-file — honest, not a host-concat fake.

## Layout

| File | Role |
|------|------|
| `GOAL.md` | Success predicate + 5-file contract + fan-out model |
| `stub/*.aura` | Intentionally wrong starters |
| `verify.sh` | Structural + `$AURA_BIN topic.aura … main.aura` |
| `dogfood.json` | `files` (5), `run_mode=cli_multi`, expect/source_res |

## Dogfood with aura-build

```bash
export AURA_BIN=/workspace/aura-grok/build_soft4048/aura   # Aura #4048 Soft Ready
aura-build llm-dogfood --project examples/projects/mini-pubsub \
  --fiber-explore 3 --explore-tools rule,llm,intent --prefer-session \
  --max-rounds 16 --worldlines 3 \
  --out trajectories/mini_pubsub_dogfood.jsonl --json

# registry alias:
aura-build llm-dogfood --task pubsub --max-rounds 16 --worldlines 3 --prefer-session --json
./examples/projects/mini-pubsub/verify.sh examples/projects/mini-pubsub/stub  # expect fail
```
