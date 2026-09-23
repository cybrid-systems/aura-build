# Iteration plan — M0–M5

## M0 — Stub floor (current)

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

- Honest Aura client interface (`mutate` / `eval` / `query`)
- Integration path when Aura binary or `/workspace/aura-grok` available
- Fallback: keep simulated backend behind the same interface

**Exit criteria**

- [ ] One real (or interface-complete stub) mutate→eval episode against Aura-shaped graph
- [ ] Trajectory `runtime.mode` reflects `aura` vs `simulated`
- [ ] No silent fake when Aura was requested

## M2 — aura-repo profile

**Deliver**

- Profile for repos with `build.py` + tests
- Multi-candidate incr-compile select-best

**Exit criteria**

- [ ] Fan-out ≥2 worldlines; fitness includes incr compile + tests
- [ ] Storm still incr (documented metric)

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
