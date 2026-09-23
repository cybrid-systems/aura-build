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

## M2 — aura-repo profile (current)

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

## M3 — Memory/harness mutate + canary (next)

**Deliver**

- L1 strategy mutation under canary
- L2 offline weight hook (load by id)
- L3 remains experimental flag-gated
- Preview: prove or keep refusing `incr_proven`; optional long-lived Aura session if binary healthy

**Exit criteria**

- [ ] Canary rejects bad L1 before default path
- [ ] Episodes record harness ids correctly

## M4 — RL export + specialist notes

**Deliver**

- Batch export (JSON array / Parquet notes)
- Specialist training notes from trajectory corpus

**Exit criteria**

- [ ] Export validates against v0 schema
- [ ] Privacy retention_class enforced in export filters
- [ ] Off-runtime devaluation documented in training notes

## M5 — TUI / ACP (deferred)

**Deliver**

- Optional TUI and ACP adapter — **after** headless trajectory loop is solid

**Exit criteria**

- [ ] Headless path remains SSOT
- Soft ≠ Restricted; no plugin-as-moat narrative
