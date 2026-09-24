# mini-exchange — 15-file aura-build dogfood (tier after mini-saga)

Miniature limit-order exchange: book, price-time match + STP, risk, ledger, fees,
halt, snapshot+replay, idempotent cloids — **15 files** (mini-saga = 10).

See `GOAL.md` for the exact stdout contract.

```bash
export AURA_BIN=/workspace/aura-grok/build_soft4054/aura
aura-build self-evolve combat --project examples/projects/mini-exchange \
  --start-session --fiber-explore 3 --fiber-llm --max-rounds 24 --no-push --json
./examples/projects/mini-exchange/verify.sh examples/projects/mini-exchange/stub  # expect fail
```
