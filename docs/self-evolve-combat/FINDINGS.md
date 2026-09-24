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
