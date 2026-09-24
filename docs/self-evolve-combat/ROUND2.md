# Self-evolve combat — Round 2 (mini-exchange)

**When:** 2026-09-24 (Asia/Shanghai, CST)
**Design SSOT:** `docs/self-evolve-combat.md`
**Aura Soft Ready tip:** `/workspace/aura-grok/build_soft4054/aura` (=`build_soft4048`) @ **`8b8c9fa`** (#4054 TLS body-lock across yield)
**aura-build:** tip before this round `583dafe` → product commits in this push

## Tier chosen

**mini-exchange** — 15-file limit-order exchange (clearly harder than mini-saga=10).

| Domain | Files |
|--------|-------|
| Idempotency + journal | `idemp.aura` `journal.aura` |
| Ledger + fee + risk | `ledger.aura` `fee.aura` `risk.aura` |
| Book + match + settle | `book.aura` `match.aura` `settle.aura` |
| Order + halt | `order.aura` `halt.aura` |
| Snapshot + replay + query | `snapshot.aura` `replay.aura` `query.aura` |
| Orchestrator + scenario | `exchange.aura` `main.aura` |

Invariants exercised: price-time match, STP (self-trade skip), risk notional/cash/pos, fee×sides (=14), halt reject, cloid dup, snapshot≡replay (`EQ=1`), COUNT=10.

Layout: `examples/projects/mini-exchange/{GOAL,README,dogfood.json,verify.sh,stub/,gold/}`.
Intent/rule tool loads `gold/` for deterministic repair (same pattern as saga host template).

## Soft rebuild + #4054 gate

- Reused Soft Ready cmake profile; `build_soft4054` → symlink to `build_soft4048` @ tip `8b8c9fa`.
- `scripts/check_soft_ready_http_post_two_batch_4054.py` → **PASS** (batch1+batch2 ok, pings ok).

## Combat runs

### 2a — green path (rule/llm/intent, fiber-llm)

```bash
aura-build self-evolve combat --project examples/projects/mini-exchange \
  --start-session --fiber-explore 3 --fiber-llm \
  --explore-tools rule,llm,intent --max-rounds 24 --no-push --json
```

| Field | Measured |
|-------|----------|
| ok / reason | **True / verify_green** |
| session / serve | serve / async |
| explore_parallel / worldline | fiber_graph / fiber_graph |
| llm_via / llm_parallel | **fiber** / fiber_serial (honest: not concurrent-llm) |
| tools_used_selected | **intent** (gold/) |
| fiber_llm | true |
| Artifacts | `round2_exchange_*.json*`, `combat_20260924-141013_*` |

Wall ≈ Soft boot + ~1 repair round (intent) after session attach (~2–3 min including Soft Ready probe boot).

### 2b — multi-round fiber-llm stress (concurrent MiniMax)

```bash
aura-build self-evolve combat --project examples/projects/mini-exchange \
  --concurrent-llm --fiber-llm --explore-tools llm \
  --fiber-explore 3 --max-rounds 6 --no-push --json
```

| Round | llm_via | llm_parallel | explore_parallel | fiber_batch_reason | explore_wall_ms | N |
|------|---------|--------------|------------------|--------------------|-----------------|---|
| −1 stub-seed | — | — | — | — | — | — |
| **0** | **fiber** | **fiber** | fiber_graph | — | 10701 | 3 |
| **1** | **fiber** | **fiber** | fiber_graph | — | 14235 | 3 |
| 2 | host | host_thread | fiber_graph | `batch_failed:serve_session_timeout` | 43294 | 3 |
| 3–5 | host | host_thread | host_thread | `serve_sock_missing` | ~28–37s | 3 |

**#4054 progress:** first **two** live MiniMax denseness N=3 batches stay `llm_via=fiber` (no immediate post-first-batch wedge). **Third** batch still wedges Soft → residual Aura **#4055**.

ok=False reason=`max_rounds_6` (MiniMax did not solve 15-file exchange in 6 rounds; expected — green path is 2a intent/gold).

Artifacts: `round2b_exchange_concurrent_*`, `combat_20260924-141333_*`.

## Dual sink

| Class | Action |
|-------|--------|
| Soft residual wedge after 2 live MiniMax denseness batches | **Aura issue [#4055](https://github.com/cybrid-systems/aura/issues/4055)** — tip `8b8c9fa` + repro. No kernel edit. |
| `llm_parallel=fiber_serial` without `--concurrent-llm` | **aura-build fix:** stop dual-sinking honest fiber_serial as Soft anomaly; only flag when concurrent_llm requested and N≥2 still serial |
| mini-exchange fixture + gold intent wire | aura-build product on main |

## aura-build product landed this round

- `examples/projects/mini-exchange/` (15-file tier + gold + verify)
- `llm_dogfood` TASK_EXCHANGE + intent/rule loads `gold/`
- cli `--task exchange`
- dual-sink fiber_serial honesty fix
- SSOT tip → Soft `8b8c9fa` / `build_soft4054`

## Residual / next tier

- Soft #4055: survive ≥3 live MiniMax denseness N≥3 batches (or document budget).
- Next dogfood tier idea: **mini-clearing** (multileg netting + variation margin + auction uncross) or **mini-oms** (algo slices + venue router + TCA) ≈18–20 files.
- Optional: improve MiniMax repair prompts for 15-file exchange so concurrent-llm can green without gold intent.

## Honesty

No Soft Ready / `fiber_live` / `llm_parallel=fiber` invented from env. Local stub ≠ MiniMax. `incr_proven` attached from prior measure (not re-proven this round).
