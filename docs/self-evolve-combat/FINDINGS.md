# Combat findings index

Append-only stamps from `aura-build self-evolve combat`.
Aura kernel edits: issue stubs only (never auto-edit).

- `20260924-111843` ok=True llm_via=None llm_parallel=None explore=None artifacts=`combat_20260924-111843_stdout.json`
- `20260924-111843` ok=True llm_via=None llm_parallel=None explore=None artifacts=`combat_20260924-111843_stdout.json`
- `20260924-111843` ok=True llm_via=fiber llm_parallel=fiber explore=fiber_graph artifacts=`combat_20260924-111843_stdout.json`
- `20260924-111900` ok=True llm_via=None llm_parallel=None explore=None artifacts=`combat_20260924-111900_stdout.json`
- `20260924-111900` ok=True llm_via=None llm_parallel=None explore=None artifacts=`combat_20260924-111900_stdout.json`
- `20260924-111900` ok=True llm_via=fiber llm_parallel=fiber explore=fiber_graph artifacts=`combat_20260924-111900_stdout.json`
- `20260924-112142` ok=True llm_via=None llm_parallel=None explore=None artifacts=`combat_20260924-112142_stdout.json`
- `20260924-112142` ok=True llm_via=None llm_parallel=None explore=None artifacts=`combat_20260924-112142_stdout.json`
- `20260924-112142` ok=True llm_via=fiber llm_parallel=fiber explore=fiber_graph artifacts=`combat_20260924-112142_stdout.json`
- `20260924-112153` ok=False llm_via=host llm_parallel=host_thread explore=fiber_graph artifacts=`combat_20260924-112153_stdout.json`

## Dig: `serve_session_timeout` after fiber-llm probe-ok (2026-09-24 Asia/Shanghai)

**Root cause class:** **Aura Soft Ready bug** (session wedge / lost async wake) — **not** aura-build client timeout too short.

| Evidence | Result |
|----------|--------|
| Soft tip | `a9975a3` `build_soft4048/aura` (#4053) |
| aura-build tip | `2630b41` |
| Combat | `combat_20260924-112153` — probe `fiber_llm_chat_ok` ~7.2s; round0 `llm_via=fiber` / `llm_parallel=fiber`; round1 `fiber_batch_reason=batch_failed:serve_session_timeout` → host fallback |
| #4053 local stub N=4 | **PASS** oneshot 208ms / batch 204ms **ratio=0.98×** |
| Stub denseness N=2 ×2 same Soft | both **ok** (~1777 / ~1767 ms) |
| MiniMax denseness N=2 batch #1 | **ok** `llm_parallel=fiber` wall **7790** ms |
| MiniMax denseness N=2 batch #2 | **`serve_session_timeout`** wall **51506** ms; Soft **alive** `S` low CPU |
| Post-fail `(+ 1 1)` | also **`serve_session_timeout`** — Soft wedged, not slow |

**Aura issue:** https://github.com/cybrid-systems/aura/issues/4054  
**Repro artifacts:** `scratch/self_evolve_combat/repro_two_batch.py`, `repro_two_batch.log`, `repro_two_batch_result.json`, `repro4053_stub_n4.log`  
**Product action:** none (do **not** bump batch timeout; Soft never replies). Wait Soft #4054; combat may keep honest host fallback after first fiber batch until Soft tip fixes wake.

- `20260924-113221` dig=soft_wedge_after_minimax_denseness_batch issue=#4054 soft=`a9975a3` ab=`2630b41`
- `20260924-141013` ok=True llm_via=fiber llm_parallel=fiber_serial explore=fiber_graph artifacts=`combat_20260924-141013_stdout.json`
- `20260924-141333` ok=False llm_via=host llm_parallel=host_thread explore=host_thread artifacts=`combat_20260924-141333_stdout.json`

## Dig: post-#4054 live MiniMax 3rd denseness batch wedge (2026-09-24 Asia/Shanghai)

**Root cause class:** residual **Aura Soft Ready** denseness/async wake under live MiniMax — local #4054 stub N=2×2 **PASS** @ `8b8c9fa`; combat concurrent-llm rounds **0–1** stay `llm_via=fiber` / `llm_parallel=fiber` (N=3); round **2** `fiber_batch_reason=batch_failed:serve_session_timeout` then Soft detach (`serve_sock_missing`).

| Round | llm_via | llm_parallel | explore_wall_ms |
|------|---------|--------------|-----------------|
| 0 | fiber | fiber | 10701 |
| 1 | fiber | fiber | 14235 |
| 2 | host | host_thread | 43294 (timeout) |

**Aura issue:** https://github.com/cybrid-systems/aura/issues/4055  
**Soft tip:** `8b8c9fa` `build_soft4054/aura`  
**Artifacts:** `scratch/self_evolve_combat/round2b_exchange_concurrent_*`, `ROUND2.md`  
**aura-build:** dual-sink no longer files Aura stubs for honest `fiber_serial` without `--concurrent-llm`.

- `20260924-141500` dig=soft_wedge_3rd_minimax_denseness_batch issue=#4055 soft=`8b8c9fa` tier=mini-exchange
- `20260924-173517` ok=True llm_via=None llm_parallel=None explore=None artifacts=`combat_20260924-173517_stdout.json`
- `20260924-173517` ok=True llm_via=None llm_parallel=None explore=None artifacts=`combat_20260924-173517_stdout.json`
- `20260924-173517` ok=True llm_via=fiber llm_parallel=fiber explore=fiber_graph artifacts=`combat_20260924-173517_stdout.json`
- `20260924-173546` ok=False llm_via=fiber llm_parallel=fiber_serial explore=host_thread artifacts=`combat_20260924-173546_stdout.json`
- `20260924-174643` ok=False llm_via=fiber llm_parallel=fiber explore=fiber_graph artifacts=`combat_20260924-174643_stdout.json`

## ROUND3 — Soft #4055 live denseness verified; mini-exchange still MiniMax residual (2026-09-24 CST)

**Soft tip:** `bd1c610` `build_soft4055/aura` — local 4054/4055 stubs PASS; live MiniMax denseness **5×N=3** all `llm_via=fiber` / `llm_parallel=fiber` (probe 6.8s; batches 5.6/4.0/6.0/5.8/3.3s). **No #4055 reopen.**

**Combat (no gold/intent):** three max_rounds_8 runs on mini-exchange; Soft fiber denseness held (run C: **8/8** fiber/fiber/fiber_graph). MiniMax residual: FILL1=filled + unbalanced parens.

**aura-build:** `a518797` multi-file repair context; `760a9ee` FILL1/parens scaffolding. Artifacts `combat_20260924-172306_*`, `173546_*`, `174643_*`, `ROUND3.md`.

- `20260924-172306` ok=False llm_via=fiber llm_parallel=fiber_serial explore=fiber_graph artifacts=`combat_20260924-172306_stdout.json`
- `20260924-173546` ok=False llm_via=fiber llm_parallel=fiber_serial explore=host_thread artifacts=`combat_20260924-173546_stdout.json`
- `20260924-174643` ok=False llm_via=fiber llm_parallel=fiber explore=fiber_graph artifacts=`combat_20260924-174643_stdout.json` soft=#4055_live_ok


## INVALID — contract_heal gold-smuggle (2026-09-24 CST) — do not claim pure-MiniMax green

**What happened:** aura-build commits `487bcf3` and `319e4a7` added `_contract_heal_exchange` that **overwrote** MiniMax fee/settle/snapshot/replay/exchange/main bodies with hand-written Alice/Bob fee-math and replay-fold (GOAL words, gold content). Offline verify of an elitist candidate reached EQ=1/FEES=14/COUNT=10 **only after** that overwrite.

**Ruling:** not pure MiniMax / no-gold. Any green or fitness jump that depended on `contract_heal` is **invalid** for the pure-MiniMax claim.

**Remediation:**
- Reverted on main: `06e27fb` (revert 319e4a7), `dde6bd2` (revert 487bcf3).
- Kept generic loop levers from `12eaaba` (per-file parse gate, elitist carry, expect-line fitness, honest `llm_parallel` aggregate).
- Product repair prompts: stripped fixture-literal targeting (FEES=14 / EQ=1 / FILL1 force / scenario narrative) from `_implicated_files` / `_interface_contracts_blob` / late focus — derive from verify KEY diffs + GOAL.md text already in the propose body.

**Valid pure-MiniMax best (pre-heal, run `combat_20260924-175921`):** best_fitness **0.7385** (FILL1…DUP/REPLAY ok; EQ=0 FEES=35 COUNT=8). Soft denseness fiber throughout; summary `llm_parallel=fiber` after aggregate fix.

- `20260924-182234` ok=True llm_via=fiber llm_parallel=fiber explore=fiber_graph artifacts=`combat_20260924-182234_stdout.json`

## INVALID green — hardcode COUNT/STP (combat_20260924-182234, 18:22–18:33 CST)

After contract_heal revert, generic-only run `combat_20260924-182234` reported `ok=True` / fitness 1.0 / `tools=['llm']` / Soft denseness fiber. **Rejected as pure-MiniMax green:** selected `main.aura` contains literal `(show "STP" 0)` and `(show "COUNT" 10)` (expect values). settle-fill was a no-op; FEES=14 came from order-path fee-rate×qty coincidence. verify.sh stdout match alone was insufficient.

**Product fix:** generic `_expect_literal_hardcode_hits` — fail structure when source shows/displays expect KEY=value as a literal (no gold). Prior best **honest** pure-MiniMax fitness remains **0.7385** (`combat_20260924-175921`) until a non-hardcode green.


## Dig: combat_20260924-183518 host_thread every round (2026-09-24 ~18:35–18:48 CST)

**Not a Soft fiber denseness repro.** After tip `9b425e1` anti-hardcode:

| Field | Measured |
|-------|----------|
| `fiber_live` | true (denseness probe OK) |
| `fiber_llm_probe` | ok ~6971ms `fiber_llm_chat_ok` |
| `fiber_batch_reason` r0 | `http_post_or_b64_missing:serve_session_timeout:None` |
| later rounds | `http_post_or_b64_missing:serve_sock_error:timed out:None` |
| `llm_via` / `llm_parallel` | **host** / **host_thread** every combat round |

Soft `--serve-async` stops answering sock/session RPC after a green in-fiber MiniMax probe when aura-build tries `ensure_http_post` + N=3 fiber batch. Honest host fallback.

**Aura:** https://github.com/cybrid-systems/aura/issues/4056 (Soft tip `bd1c610` / `build_soft4055`).

**Elite carry:** traj `best_ever` rose to **0.6308** and held while some later *round candidates* maxed at 0.5231 — historical elite fitness must be reported separately from selected-round fitness. Product now logs `elite_fitness` / `elite_id` per rounds_log entry.

**aura-build mitigation (does not invent fiber):** longer Soft sock timeout for `ensure_http_post` (20s→90s) before host fallback.


## Dig close-out — round3i host_thread (Aura #4056) + elite vs candidate (2026-09-24 CST)

### Why `llm_parallel=host_thread` on combat_20260924-183518
Not session-start failure. Soft `--serve-async` attached (`soft_ready_ok`, shared_ast probes OK). Measured sequence:

1. `fiber_live=true`
2. `fiber_llm_probe` **ok** ~6971ms (`fiber_llm_chat_ok`)
3. Concurrent N=3 fiber MiniMax batch / `ensure_http_post` → Soft RPC fails:
   - r0: `http_post_or_b64_missing:serve_session_timeout:None`
   - later: `http_post_or_b64_missing:serve_sock_error:timed out:None`
4. Honest fallback: `llm_via=host` / `llm_parallel=host_thread` every combat round

**Aura issue:** https://github.com/cybrid-systems/aura/issues/4056 (Soft tip `bd1c610` / `build_soft4055`). Soft can wedge mid-combat at ~50% CPU with no sock reply (observed on 3j after several green fiber rounds).

**Do not count 3i as a Soft fiber denseness repro.**

### Elite carry vs round-candidate dips
On 3i/3j, **selected-round max fitness can dip** (e.g. candidates 0.08–0.16) while **implied elite ceiling** stays flat once reached (3j: elite 0.5231 while a peer candidate scored 0.08). Elitist `elite_sources` / `elite_fitness` in `llm_dogfood` prevents propose base regression; rounds_log now records `elite_fitness`/`elite_id` (`7d94019`). Always report **elite_fitness separately** from per-round selected fitness.

### Fiber runs after `9b425e1` (honest)
| Run | Artifact | Soft denseness LLM | Best real cand | Elite (implied) | Notes |
|-----|----------|--------------------|----------------|-----------------|-------|
| 3i | `combat_20260924-183518` | **host_thread** all | ~0.63 (incl. noise) | ~0.6308 | Soft sock timeout after probe — **not fiber** |
| 3j | `combat_20260924-185110` | fiber×6, fiber_serial×2, host_thread×2 | **0.5231** | **0.5231** | Soft #4056 mid-run hang; SIGTERM 143 after Soft CPU wedge |
| 3k | `combat_20260924-191515` | fiber (in progress) | TBD | TBD | Second fiber attempt after Soft restart |

**Honest pure-MiniMax best still:** **0.7385** @ `combat_20260924-175921` (fiber). Hardcode green `182234` and any contract_heal path remain **invalid**.

