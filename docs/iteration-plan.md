# Iteration plan — M0–M5

## M0 — Stub floor

**Deliver**

- Headless CLI: `aura-build run --prompt ...`
- Trajectory JSONL writer + schema validate
- Fake worldline select-best demo (simulated if Aura not wired)
- CI smoke (pytest)

**Exit criteria**

- [x] `pip install -e .` + `aura-build run` writes valid episode under `trajectories/`
- [x] `pytest` + `scripts/smoke.sh` green
- [x] Docs encode north star (anti-postman, dogfood Aura, L1/L2/L3, deny plugin-as-moat)

## M1 — Real Aura mutate/eval

**Deliver**

- Honest `RuntimeBackend` protocol: `SimulatedBackend` + `AuraBackend`
- `AuraBackend` shells to aura binary with tiny `mutate:rebind` + `eval-current` program
- Fallback: simulated behind the same orch surface; **no silent fake when `--mode aura`**
- Trajectory `runtime.mode` records the backend actually used (`requested_mode` kept for auto)

**Exit criteria**

- [x] Interface-complete mutate→eval behind orch; live shell when `AURA_BIN` probes clean
- [x] Trajectory `runtime.mode` reflects `aura` vs `simulated`
- [x] No silent fake when Aura was requested (`mode=aura` → `AuraUnavailable` / exit 2)
- [x] CI simulated smoke stays green; optional `aura` job skips if binary missing

**Honesty note:** M1 `AuraBackend` is a **subprocess bridge**, not fiber-live multi-worldline on one FlatAST. Do not claim live worldlines yet.

## M2 — aura-repo profile

**Deliver**

- Profile for repos with `build.py` + tests (`--profile aura-repo`)
- Worldline API: parent snapshot → N candidates with **stable refs** on a shared workspace dir
- Discard losers documented in trajectory (`discarded[]`)
- Fitness hooks wrapping `build.py` / compile check; simulated fallback when Aura/toolchain broken (e.g. GLIBCXX)
- Metric placeholders: `compile_ms`, `incr_claimed`, **`incr_proven=false`** (explicit until storm-still-incr is measured)
- Session model recorded: `shared_workspace_subprocess` (default) — not claiming long-lived Aura multi-eval yet

**Exit criteria**

- [x] Fan-out ≥2 worldlines with `parent_id` + `stable_ref`; fitness includes compile_ms + tests fields
- [x] `incr_proven=false` always set in M2 trajectories/docs (storm-still-incr not yet proven)
- [x] Prefer stable-ref continuity on shared workspace vs mail/worktree; losers discarded in episode
- [ ] True incr-compile proof / fiber-live single FlatAST session (deferred — do not fake)

**Honesty note:** M2 shared workspace is **not** fiber-live FlatAST. Default remains simulated-green CI. Live `build.py` hook uses a cheap discovery command unless callers pass a real compile command.

## M3 — Memory/harness mutate + canary (current)

**Deliver**

- Harness config as mutable object: `worldline_count`, `fitness_weights`, `routing` (when to use aura vs simulated)
- Propose mutate → canary episode on **shadow** profile → commit or heal/discard
- Default **AUTOPROMOTE OFF**; `AURA_BUILD_AUTOPROMOTE=1` / `--autopropote` for demos
- Every harness change writes `mid` + trajectory `harness.actions[]`
- Memory store: per-user/profile keyed notes (file-backed JSON under `.aura-build/memory/`)
- L2 offline specialist weight: **stub hook by model id only** (no training)
- L3 remains experimental / refused in orch
- Keep **`incr_proven=false`**; do not claim fiber-live

**Exit criteria**

- [x] Canary rejects bad L1 (e.g. `worldline_count=0`) before default/live path
- [x] Episodes record harness ids / mid / actions correctly
- [x] AUTOPROMOTE default off; discard on pass unless flag/env
- [x] Memory get/set via CLI + orch; L2 stub resolves by id
- [ ] Fiber-live FlatAST / storm-still-incr proof (still deferred)
- [ ] Real L2 weight load / training (deferred to M4+)

**Honesty note:** M3 canary is a **shadow harness episode**, not fiber-live multi-worldline. Committing harness JSON under `.aura-build/` is not promoting online L3 weights.

## M4 — RL export + specialist notes (next)

**Deliver**

- Batch export (JSON array / Parquet notes)
- Specialist training notes from trajectory corpus
- Real L2 weight artifact promotion notes (still offline)

**Exit criteria**

- [ ] Export validates against v0 schema
- [ ] Privacy retention_class enforced in export filters
- [ ] Off-runtime devaluation documented in training notes
- [ ] RL export pipeline stubs consumed by offline jobs (no online L3)

## M5 — TUI / ACP (deferred)

**Deliver**

- Optional TUI and ACP adapter — **after** headless trajectory loop is solid

**Exit criteria**

- [ ] Headless path remains SSOT
- Soft ≠ Restricted; no plugin-as-moat narrative
