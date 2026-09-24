# Self-evolve combat — Round 1

**When:** 2026-09-24 (CST)
**Design SSOT:** `docs/self-evolve-combat.md` @ aura-build `76846c1`
**Aura Soft Ready tip:** `/workspace/aura-grok/build_soft4048/aura` @ **`a9975a3`** (#4053 denseness async http-post + body mutex unlock)
**aura-build:** kickoff `f575779` → design `76846c1` → product fix (this commit)
## What ran

1. Soft zombies killed; `aura-build session start` Soft Ready bin  
   Measured: `session_model=serve`, `serve_mode=async`, `serve_cross_session_shared_ast=true`, `serve_same_session_mutate_ok=true`
2. **1a** mini-saga `llm-dogfood --prefer-session --fiber-explore 3 --fiber-llm --explore-tools rule,llm,intent --worldlines 3 --max-rounds 8`  
   Wall ≈ **93s**, green in 1 round (intent selected; fiber denseness live)
3. **1b** mini-cache `--concurrent-llm --explore-tools llm --fiber-llm` (pre-fix)  
   Wall ≈ **93s**; probe ok but proposes **`llm_via=host` / `llm_parallel=host_thread`**, `explore_wall_ms≈29543`, `llm_calls_parallel=3`
4. Root cause (same Soft session, real MiniMax):  
   - tiny chat batch → `llm_parallel=fiber`, wall ≈ oneshot  
   - ~5KB propose Soft **string-inline** body → MiniMax bad_request / `no_content_in_response`  
   - `AURA_BUILD_FIBER_LLM_MODE=write_file` OK; **`_INLINE_BODY_MAX=2000`** (request read-file, response in-memory join) OK + batch wall ≈ oneshot
5. **1c** mini-cache concurrent fiber-llm **after fix**  
   Wall ≈ **96s**; **`llm_via=fiber`**, **`llm_parallel=fiber`**, `llm_parallel_ok=true`, `llm_calls_parallel=3`, `explore_wall_ms≈9603` (~3× vs host_thread 29.5s)

Orchestration stub: `scripts/self_evolve_combat.sh` (P1 thin; Soft required; no push).

## Honesty stamps (measured)

| Field | 1a mini-saga | 1b pre-fix | 1c post-fix |
|-------|--------------|-------------|--------------|
| `session_model` / `serve_mode` | serve / async | serve / async | serve / async |
| `explore_parallel` / worldline | fiber_graph | fiber_graph | host_thread (LLM path independent) |
| `fiber_llm` probe | ok ~7.2s | ok ~6.8s | ok |
| `llm_via` | host (intent won) | **host** (inline fail → fallback) | **fiber** |
| `llm_parallel` | host_thread | host_thread | **fiber** |
| `incr_proven` | true via **attached** prior `storm_incr_valid_measured` (report_ts 2026-09-23) — not re-proven this combat | same | same |

No Soft Ready / fiber_live / `llm_parallel=fiber` invented from env. Local stub ≠ MiniMax.

## Dual sink

| Class | Action |
|-------|--------|
| Soft string-inline ~5KB JSON → MiniMax bad_request | **aura-build fix:** `_INLINE_BODY_MAX` 48k→2k + `fiber_batch_reason` stamp (this commit). No Aura kernel edit. |
| Soft hang/SEGV vs #4053 | None observed this round — no Aura issue filed |
| Stamp `self-evolve` ≠ combat | Design doc already separates; combat is SSOT |

## Artifacts

- `scratch/self_evolve_combat/round1_*.json*` — saga  
- `scratch/self_evolve_combat/round1b_*` — pre-fix cache  
- `scratch/self_evolve_combat/round1c_*` — post-fix fiber parallel  

## Next

- **P1 wire:** LANDED — `aura-build self-evolve combat` (Soft required, `--no-push` default, findings under `scratch/self_evolve_combat/`)
- **P2 continue:** aura-build harness/doc honesty goal in same Soft session; denseness+`fiber_llm` same round; never claim N≥4 wall-parallel without measure
- **P3:** Aura issues only for confirmed kernel/stdlib; keep aura-build honesty fixes on main

## Residual risks

- Denseness `fiber_graph` and `llm_parallel=fiber` are independent stamps  
- Soft multi-worker denseness still not production Ready  
- Attached `incr_proven` can look fresh — check `prove_incr.report_ts`  
- Soft status `value` with raw `{` still fragile (aura-build #1)

## Dig follow-up (2026-09-24): fiber-llm second-batch timeout

Combat `20260924-112153` round1 `serve_session_timeout` after probe-ok / round0 fiber OK is **Soft wedge** (Aura [#4054](https://github.com/cybrid-systems/aura/issues/4054)), not aura-build timeout. Local-stub #4053 N=4 still PASS @ `a9975a3`. See FINDINGS.md dig section.
