# Iteration plan — M0–M5 + Post-M5 + Aura kernel

> **Kernel = Aura.** Core orch / worldline / prove / harness / traj / memory / L2 live under `aura/*.aura`. Python is thin host only (no orch fallback). See README.

## Status table (M0–M5 + Post-M5)

| Milestone | Theme | Status | Honest note |
|-----------|-------|--------|-------------|
| **M0** | Stub floor — CLI + trajectory JSONL + simulated select-best | **done** | Simulated only |
| **M1** | RuntimeBackend — Simulated + Aura subprocess bridge | **done** | Not fiber-live |
| **M2** | Worldline shared workspace + aura-repo profile | **done** | `incr_proven=false`; stable_ref ≠ fibers |
| **M3** | Harness canary + memory + L2 stub-by-id | **done** | AUTOPROMOTE default OFF |
| **M4** | RL/batch export + privacy + specialist notes | **done** | No training; no online L3 |
| **M5** | TUI/ACP skeleton + L2 offline metadata plug | **done** | Metadata-only weights; TUI is status stub |
| **Post-M5** | storm-still-incr prove-or-refuse + doctor + fiber probe | **done (harness)** | `incr_proven` stays false until measured; GLIBCXX ⇒ fail-closed |

**Still refused / deferred:** true `--serve-async` Soft multi-worker + cross-session shared FlatAST (`serve_cross_session_shared_ast`); `incr_proven=true` without explicit incr-valid signal; real L2 tensor/mmap (`stub=False`); online L3; full Textual/rich TUI. **Shipped MVP:** host-managed long-lived `--serve` attach (`session_model=serve`, `aura-build session *`) — see [optimal-dev-loop.md](optimal-dev-loop.md). (`fiber_graph` worldlines require honest denseness probe — env alone cannot elevate.)

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

## M3 — Memory/harness mutate + canary

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
- [ ] Real L2 tensor load / training (deferred)

**Honesty note:** M3 canary is **not** fiber-live multi-worldline. L1 live path uses `std/hot-strategy` (register/swap/heal + last-good) with `harness.json` as durable mirror; traj records `l1_backend`. Committing harness JSON is not promoting online L3 weights and never invents `fiber_live` / `incr_proven`.

## M4 — RL export + specialist notes

**Deliver**

- CLI: `aura-build export` — JSONL → JSON array (always) + Parquet when pandas/pyarrow present
- Privacy filters **default ON**: strip absolute paths → placeholders; redact token/key patterns; `--include-raw` for local dogfood only
- Specialist training notes: fields distillers need (actions, fitness, worldline outcomes, `harness.mid`, `incr_proven=false` honesty)
- L2 weight artifacts: stub-by-id retained; document plug points for real weights; **no training loop**
- Keep `incr_proven=false`; no fiber-live FlatAST claim; no online L3 weight updates

**Exit criteria**

- [x] Export validates against v0 schema
- [x] Privacy redaction default ON; retention_class preserved; `--include-raw` opt-out
- [x] Off-runtime devaluation documented in [specialist-training-notes.md](specialist-training-notes.md)
- [x] RL export pipeline writes JSON (+ optional Parquet) for offline jobs (no online L3)
- [ ] Real L2 tensor load (`stub=False`) (deferred — M5 is metadata-only)
- [ ] Fiber-live FlatAST / storm-still-incr proof (still deferred)

## M5 — TUI / ACP + L2 offline metadata plug (current / closing)

**Deliver**

- Minimal headless-compatible `aura-build tui` — stdlib status stub (session + last traj path); not a full Textual loop
- ACP hooks documented + CLI: `start` / `status` / `worldlines` / `discard` / `export` / `hooks` — wired to existing orch/export/worldline surfaces
- L2 offline metadata: load/promote stub artifact at `.aura-build/weights/<id>.json` (`id`, `created`, `notes`); promotion refuses `l3_online=true` corpora
- Still **no** training; **no** tensor load (`stub=True` always); **no** online L3; **no** fake `incr_proven=true`; **no** fiber-live claim

**Exit criteria**

- [x] Headless path remains SSOT (`run` / `export` / harness canary)
- [x] Soft ≠ Restricted; no plugin-as-moat narrative (TUI/ACP are thin host adapters)
- [x] L2 metadata loader sets `artifact_present=True` when JSON loads; **`stub` stays True** (no weight bytes)
- [x] Offline promote excludes `l3_online=true` by default
- [ ] Real L2 tensor/mmap load → `stub=False` (deferred past M5)
- [ ] Full TUI (Textual/rich) / editor ACP embed (deferred)
- [ ] Fiber-live FlatAST / storm-still-incr proof (still deferred)

## Post-M5 — prove-or-refuse (storm-still-incr)

**Deliver**

- Measurement harness: `aura-build prove-incr` + `docs/storm-still-incr.md` + `scripts/prove_incr.sh`
- Fail-closed when Aura unhealthy (GLIBCXX / missing): report `incr_proven=false` + reason; CI-green
- Healthy path: N rapid mutate+eval under concurrent worldline pressure; `incr_proven=true` **only** with explicit incr-valid signal every cycle
- Honest fiber denseness probe (`fiber:spawn`+join + same-FlatAST multi); `fiber_live` only when probe works; env cannot elevate
- Slice 3: orch/worldline lift to `worldline_backend=fiber_graph` when denseness live; else file layout
- `aura-build doctor` surfaces probe + last report; ACP/TUI honesty overlays last report

**Exit criteria**

- [x] Fail-closed path tested and CI-green (`tests/test_prove_incr.py`)
- [x] Report written under `.aura-build/prove-incr-latest.json`
- [x] Never claim fiber-live / incr_proven without measurement
- [ ] Real FlatAST incr telemetry from Aura (deferred)
- [x] Honest fiber denseness probe in prove-incr / doctor (slice 2)
- [x] Lift worldlines to fiber graph when `fiber_live` (`worldline_backend=fiber_graph|file`); serve-async long-lived session still deferred
- [ ] Auto-attach prove report into every orch episode (deferred; opt-in later)

**Honesty note:** On boxes where the Aura binary hits `GLIBCXX_` mismatch, expect `incr_proven=false` forever until a healthy runtime is measured. Do not flip the flag by hand.



## Post-M5+ — Aura kernel rewrite

**Deliver**

- `aura/` modules: `main`, `orch`, `worldline`, `prove`, `harness`, `traj`, `memory`, `l2`, `util`
- Thin Python `kernel.py` + CLI prefer Aura when binary+sidecar healthy
- Trajectory JSONL still `trajectory.v0`; `runtime.kernel=aura` on kernel path
- Honest prove-incr in-process (`incr_proven` only with measured epoch/invalidate deltas)
- CI-safe: host pytest + refuse path when no `AURA_BIN`; Aura episodes skip; optional live Aura job

**Exit criteria**

- [x] Primary `aura-build run` executes Aura kernel when Aura available
- [x] `harness-mutate` / `prove-incr` / `doctor` / `harness-show` / `export` / `acp` Aura-first (same host policy as `run`)
- [x] Docs say kernel=Aura; list Aura-first CLIs vs Python-only surfaces
- [x] Simulated + prove path smoke green (CI fallback + live when sidecar present)
- [ ] Delete remaining Python orch once GHA provisions Aura (deferred shrink)


## Post-M5++ — self-evolve (aura-build dogfood)

**Deliver**

- Aura-first `aura-build self-evolve`: dogfood mutate on this repo (harness L1
  canary and/or worldlines over the aura-build tree)
- Materialize winner into the git worktree (`aura/self_evolve_stamp.aura` + traj)
- Verify (host smoke / prove-incr / kernel episode) — red ⇒ no commit/push; traj reason
- Commit on `main` with traj id / harness mid / honesty flags (`incr_proven` /
  `fiber_live` never invented); `runtime.kernel=aura`
- Push `origin main` when verify green (skip CI wait); `--no-push` / `--no-commit` for dry runs
- Thin Python CLI only; refuse without `AURA_BIN`
- Tests: refuse + `--no-push` path CI-safe; live push not required in pytest

**Exit criteria**

- [x] `self-evolve` Aura kernel command + thin host commit/push edge
- [x] `--no-push` / `--no-commit` / `--verify none|smoke|prove|kernel`
- [x] Never fake `incr_proven` / `fiber_live`
- [ ] Live fiber-multi worldline materialize (still deferred — stamp + L1 dogfood first)


## Post-M5++ — long-lived serve attach (optimal loop MVP)

**Deliver**

- SSOT [optimal-dev-loop.md](optimal-dev-loop.md)
- Host-managed `aura --serve`: `aura-build session start|status|stop|dogfood`
- In-session verify path for dogfood when session live (`via=serve_session`)
- Honesty: `session_model=serve`, `serve_session_ok` from live pid (not env)
- mini-* llm-dogfood demoted to fixture / regression

**Exit criteria**

- [x] Docs SSOT merged
- [x] Session start/status/stop on box with AURA_BIN
- [x] Session dogfood closed loop + cold compare
- [ ] True Soft Ready serve-async + orch/project shared FlatAST (`serve_cross_session_shared_ast`); measured Soft refuse + same-session mutate ok shipped
