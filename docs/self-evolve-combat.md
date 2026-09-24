# Self-evolve combat (SSOT)

> **Combat** = combine Aura Soft session + fiber explore + fiber LLM + worldlines
> + traj + dual sink (aura-build self-improve **and** Aura/stdlib issue filing)
> in a **closed loop on a real Soft Ready tip**.
>
> This doc is the SSOT for combat self-evolve. The existing
> `aura-build self-evolve` (`aura/self_evolve.aura` + host commit/push edge) remains
> **L1/stamp dogfood** (stamp + simulated fitness + harness canary) — it is **not**
> fiber-live combat. Do not pretend stamp path stamps `fiber_live` / `fiber_graph`
> from env.

**Tips this inventory assumes (honest):**

| Layer | Tip |
|-------|-----|
| Aura Soft Ready binary | `/workspace/aura-grok/build_soft4054/aura` (=`build_soft4048`) @ **`8b8c9fa`** (#4054 TLS body-lock across yield; #4053 async http-post; #4048 denseness; #4047 Soft Ready profile) |
| aura-build | main @ tip after P1 wire (`self-evolve combat` CLI + ROUND1 fix `9cc096c`) |

Rebuild Soft only if that binary is missing/outdated. Soft honesty banner stays **Soft Ready**.

---

## A. Capability inventory (what combat may honestly combine today)

| # | Capability | Honest stamp / condition | Notes |
|---|------------|--------------------------|-------|
| 1 | Soft Ready `--serve-async` attach | `session_model=serve`, measured `serve_mode=async` (Soft Ready profile #4047+) | Env cannot elevate Soft Ready / async. Older tips → `serve_mode=sync`. |
| 2 | Same-session `mutate:rebind` + `eval-current` | `worldline_backend=serve_mutate_rebind`, `cold_spawns=0`, `serve_same_session_mutate_ok` | Anti-postman primary path. |
| 3 | Denseness `fiber:spawn` / `join` | `worldline_backend=fiber_graph` / `explore_parallel=fiber_graph` **only** when denseness probe ok (#4048 Soft Ready) | On probe fail → honest `host_thread`. Never invent `fiber_live` / `fiber_graph`. |
| 4 | Soft in-fiber MiniMax via `http-post` | `llm_via=fiber` after #4053 + aura-build fiber_llm base64 in-memory join; `llm_parallel=fiber` **only** when N≥2 batch wall ≈ concurrent; else `fiber_serial` | Local stub ≠ MiniMax. Do not claim wall-parallel without measuring real MiniMax. |
| 5 | Explore tools ≠ agents | `--explore-tools rule,llm,intent` strategies on fibers; stamp `tools_used` | Not a three-agent product. |
| 6 | Worldline select-best + trajectory.v0 | Episodes under `trajectories/` / combat scratch; `runtime.*` honesty fields | Off-Aura IDs/snapshots devalue. |
| 7 | L1 `std/hot-strategy` swap/heal canary | Optional; **AUTOPROMOTE default OFF** | Propose → swap → canary → heal\|commit mirror. |
| 8 | Host thin | Session PID/marker, MiniMax propose fallback (`llm_via=host`), git commit/push edge | MiniMax = **propose-only**; never loop controller. |
| 9 | Doctor / prove honesty | `incr_proven`, `fiber_live`, `serve_*` measured only | Never env-elevate. |

### Still deferred / refuse

- Soft multi-worker denseness as **production Ready** (Soft Ready auto workers=1 path is the measured dogfood surface).
- `incr_proven=true` without storm-still-incr measure.
- Cross-session shared FlatAST (`serve_cross_session_shared_ast`) if unmeasured.
- L3 online weight claims.
- Fake wall-parallel (`llm_parallel=fiber` without N≥2 measured concurrent batch).
- Self-evolve / push of **Aura kernel** from aura-build combat (never).
- Inventing Soft Ready / `fiber_live` / `fiber_graph` from env markers alone.

---

## B. Combat loop (one picture)

```
Soft serve attach (Soft Ready tip 8b8c9fa+)
  → goal / predicate (real tests or in-session eval)
  → fiber:spawn N explorers (tools: rule|llm|intent; optional --fiber-llm)
  → in-session verify / select-best
  → traj stamp (session_model, worldline_backend, llm_via, llm_parallel, fiber_live…)
  → dual sink:
       (1) aura-build product winner → verify → commit+push main (self-improve)
       (2) Aura/stdlib anomalies → issue draft / file on cybrid-systems/aura (no silent kernel edits)
  → L1 harness canary optional (propose→swap→canary→heal|commit mirror)
```

Primary CLIs for combat (reuse before rewriting stamp `self-evolve`):

```bash
export AURA_BIN=/workspace/aura-grok/build_soft4054/aura

# Kill Soft --serve / --serve-async zombies first
pkill -f 'aura .*--serve' || true

aura-build session start --aura-bin "$AURA_BIN"
aura-build session status --json

# Round combat: Soft + fiber explore + fiber-llm on a concrete goal
aura-build llm-dogfood \
  --project examples/projects/mini-saga \
  --prefer-session --fiber-explore 3 --fiber-llm \
  --explore-tools rule,llm,intent \
  --worldlines 3 --max-rounds 8 \
  --out scratch/self_evolve_combat/roundN_traj.jsonl --json \
  --env-file "$HOME/.config/aura-build/minimax.env"

# Or pursue (same-session mutate path; optional --with-llm)
aura-build pursue --goal "…" --prefer-session --worldlines 3 --max-rounds 2 --json

aura-build session stop
```

`--no-push` default for first combat promote path; document promote after green verify.

---

## C. Dual feedback protocol

| Finding class | Action |
|---|---|
| Soft hang / SEGV / serial HTTP / mutex / stdlib wrong | File Aura issue on `cybrid-systems/aura` with tip SHA + repro; aura-build stamps honest fallback (`fiber_serial`, `host_thread`, `llm_via=host`) |
| aura-build parse / CLI / honesty / fiber_llm | Fix on **aura-build `main`** in the same combat arc; commit+push when green |
| Ambiguous layer | Prefer Aura issue + aura-build honesty stamp; **do not mix layers** (no silent kernel edit inside aura-build) |

Hard constraints (memory / three-layer):

- Self-evolve / push **only** `cybrid-systems/aura-build` main — never self-evolve Aura kernel.
- Aura runtime bugs → **GitHub issues** on `cybrid-systems/aura` (stdlib surface notes OK); do not “顺便” fix language/GC/scheduler in aura-build.
- MiniMax = propose-only; never loop controller.
- Narrow path: success = closed-loop demos with this runtime; no L3 online claim; no Aura LLM pretrain.

---

## D. Phases

| Phase | What | Done when |
|-------|------|-----------|
| **P0 Design** | This doc + links from architecture / optimal-dev-loop / iteration-plan | Merged on main |
| **P1 Wire combat mode** | `aura-build self-evolve combat` thin host orchestrator (reuses `llm-dogfood` + Soft session APIs): requires Soft `serve_attach_ok` (or `--start-session`); one closed loop; traj + findings under `scratch/self_evolve_combat/` + `docs/self-evolve-combat/FINDINGS.md`; `--no-push` default (`--push` only after verify green + aura-build materialize); dual-sink Aura issue stubs (no kernel edit); stamp `self-evolve` unchanged | **CLI landed** — see §P1 below |
| **P2 Dogfood round 1** | Soft Ready + fiber explore + fiber-llm on concrete goal (prefer escalate mini-saga **or** aura-build harness/doc honesty fix — not simulated stamp). Capture wall ratios; if Soft regresses vs #4053, file Aura issue | `ROUND1.md` + traj honesty stamps |
| **P3 Self-improve** | Land aura-build fixes from round-1 failures; leave Aura issues open for kernel | Fixes on main; Aura issues filed |

P1 CLI landed as `aura-build self-evolve combat` (`src/aura_build/self_evolve_combat.py`). `scripts/self_evolve_combat.sh` remains a thin wrapper calling the CLI. Aura kernel rewrite of simulated `self_evolve.aura` still **not** required.

---

## E. Acceptance for “designed”

- [x] Doc merged on main with inventory + loop + dual sink + phases.
- [x] Explicit: current stamp `self-evolve` = L1/stamp dogfood; **combat is the new SSOT path**.
- Links: [architecture.md](architecture.md) Self-evolve section; [optimal-dev-loop.md](optimal-dev-loop.md) See also; [iteration-plan.md](iteration-plan.md) Post-M5++ self-evolve (combat = next gate).

---

## P1 CLI (landed)

```bash
export AURA_BIN=/workspace/aura-grok/build_soft4054/aura

# Refuse without Soft attach (exit 2)
aura-build self-evolve combat --json

# Start Soft then combat (kills zombies when starting)
aura-build self-evolve combat --start-session --project examples/projects/mini-cache \
  --fiber-explore 3 --concurrent-llm --fiber-llm \
  --env-file "$HOME/.config/aura-build/minimax.env" --json

# CI-safe plan / refuse path (no live Soft required)
aura-build self-evolve combat --dry-run --json

# Stamp L1 path unchanged:
aura-build self-evolve --prompt "…" --no-push
```

Flags: `--no-push` default (`--push` / `--no-push` BooleanOptionalAction); `--start-session`;
`--stop-session`; `--out-dir` (default `scratch/self_evolve_combat/`); dual-sink writes
`combat_*_AURA_ISSUE_STUB.md` for human/`gh issue create` — never auto-edits Aura.

- [x] P1 CLI `aura-build self-evolve combat` on main (thin Python orchestrator).
- [x] Refuse without `serve_attach_ok`; `--dry-run` CI-safe; stamp path unchanged.

---

## See also

- [optimal-dev-loop.md](optimal-dev-loop.md) — long-lived serve + fiber explore honesty
- [soft-ready-gate.md](soft-ready-gate.md) — Soft Ready fail bits / measured refuse
- [trajectory-protocol-v0.md](trajectory-protocol-v0.md) — episode fields
- [architecture.md](architecture.md) — layers + stamp self-evolve (non-combat)
- [iteration-plan.md](iteration-plan.md) — phase checklist
