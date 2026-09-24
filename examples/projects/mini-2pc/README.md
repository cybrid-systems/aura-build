# mini-2pc — 7-file aura-build dogfood project (magnitude jump)

A **mini** two-phase commit protocol split across **seven files** — an
order-of-magnitude harder Soft dogfood than mini-pubsub (5-file fan-out) or
mini-queue (4-file lease).

Success = stdout prints exactly:

```
RUN1=commit
STATE1=committed
RUN2=abort
STATE2=aborted
LOG=abort
RECOVER=aborted
POISON=abort
COUNT=5
```

with WAL log ops in `log.aura`, participants in `part-a.aura` / `part-b.aura`,
vote collection in `vote.aura`, coordinator in `coord.aura`, crash-recovery
finish in `recover.aura`, and `main.aura` calling those ops (not bare hardcoded
display lines). See `GOAL.md`.

## Why order-of-magnitude harder vs mini-pubsub

| | mini-pubsub | **mini-2pc** |
|--|-------------|--------------|
| Files | 5 | **7** |
| Domains | topic + sub + pub + deliver | **log + part-a + part-b + vote + coord + recover + main** |
| Coupling | fan-out + unsubscribe | **cross-file prepare→vote→decide→WAL→commit/abort→recover** |
| Failure modes | miss / wrong COUNT | **poison refuse, deny-b abort, sticky always-commit, dead log, idle recover** |
| State machine | mailbox FIFO | **idle→prepared→{committed\|aborted}** × 2 + decision log |

## How multi-file actually runs

```bash
$AURA_BIN log.aura part-a.aura part-b.aura vote.aura coord.aura recover.aura main.aura
```

`verify.sh` uses CLI multi-file — honest, not a host-concat fake for cold SSOT.

## Layout

| File | Role |
|------|------|
| `GOAL.md` | Success predicate + 7-file 2PC contract |
| `stub/*.aura` | Intentionally wrong starters |
| `verify.sh` | Structural + `$AURA_BIN log.aura … main.aura` |
| `dogfood.json` | `files` (7), `run_mode=cli_multi`, expect/source_res |

## Dogfood with aura-build

```bash
export AURA_BIN=/workspace/aura-grok/build_soft4048/aura   # Aura #4048 Soft Ready
aura-build llm-dogfood --project examples/projects/mini-2pc \
  --prefer-session --fiber-explore 3 --worldlines 3 --max-rounds 20 \
  --out trajectories/mini_2pc_dogfood.jsonl --json

# registry aliases:
aura-build llm-dogfood --task 2pc --max-rounds 20 --worldlines 3 --prefer-session --json
aura-build llm-dogfood --task twopc --max-rounds 20 --worldlines 3 --prefer-session --json
./examples/projects/mini-2pc/verify.sh examples/projects/mini-2pc/stub  # expect fail
```
