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

## M1 — Real Aura mutate/eval (current)

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

- Profile for repos with `build.py` + tests
- Multi-candidate incr-compile select-best on a shared Aura workspace (not N cold shells)
- Fitness includes incr compile ms + tests; document storm-still-incr metric

**Exit criteria**

- [ ] Fan-out ≥2 worldlines; fitness includes incr compile + tests
- [ ] Storm still incr (documented metric)
- [ ] Prefer stable-ref continuity across candidates vs mail/worktree

## M3 — Memory/harness mutate + canary

**Deliver**

- L1 strategy mutation under canary
- L2 offline weight hook (load by id)
- L3 remains experimental flag-gated

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
