# Architecture

## Layers

```
┌─────────────────────────────────────────────────────────┐
│  Host (thin)                                            │
│  CLI / CI / (later TUI·ACP) — no business moat here     │
└──────────────────────────┬──────────────────────────────┘
                           │ prompts, policy, I/O
┌──────────────────────────▼──────────────────────────────┐
│  Aura control plane (aura-build orch)                   │
│  scout → mutate → eval → select-best                    │
│  worldline fan-out (fibers) · anti-postman default      │
└──────────────┬───────────────────────────┬──────────────┘
               │                           │
┌──────────────▼──────────────┐ ┌──────────▼──────────────┐
│  Live FlatAST (Aura)        │ │  Trajectory store        │
│  query/mutate · stable IDs  │ │  episode JSONL / export  │
│  concurrency · audit · incr │ │  privacy · devaluation   │
└──────────────┬──────────────┘ └──────────┬──────────────┘
               │                           │
┌──────────────▼───────────────────────────▼──────────────┐
│  Evolving memory / harness                              │
│  L1 strategy code · L2 offline weights · L3 online exp. │
└─────────────────────────────────────────────────────────┘
```

## Host thin

The host process is a **thin** adapter: argparse/CI entrypoints, path wiring, exit codes. Surface shape may follow grok-build (headless → CI → ACP later). Product value does **not** live in host chrome. Soft ≠ Restricted; deny plugin-as-moat.

## Aura control

`orch` owns the episode loop:

1. **Scout** — read task + optional harness hints (L1/L2).
2. **Mutate** — propose N worldline mutations via `RuntimeBackend` (`SimulatedBackend` or `AuraBackend` shelling `mutate:rebind`).
3. **Eval** — fitness: tests, incr-compile cost, audit constraints (`eval-current` when Aura).
4. **Select-best** — collapse to one worldline; append trajectory (`runtime.mode` = backend actually used).

### RuntimeBackend (M1)

| Backend | When | Honesty |
|---------|------|---------|
| `SimulatedBackend` | `--mode simulated` or `auto` fallback | Fake fitness; not live FlatAST |
| `AuraBackend` | `--mode aura` / successful `auto` probe | Subprocess `aura` + tiny program; **not** fiber multi-worldline yet |

Integration points: `AURA_BIN` / `--aura-bin`, `scripts/aura_m1_mutate_eval.aura`, primitives `set-code` → `mutate:rebind` → `eval-current`. See `src/aura_build/runtime.py` module docstring.

### Worldlines (M2 API)

A worldline is a **candidate live-object history**, not a git worktree. Default is anti-postman: keep candidates on the floor with stable IDs. Git/mail export is an escape hatch for humans and external CI, not the primary concurrency model.

`WorldlineWorkspace` (`src/aura_build/worldline.py`):

1. Snapshot **parent** under a shared workspace dir
2. Fork **N candidates** with `stable_ref` + `parent_id`
3. Eval each (profile fitness / backend)
4. **Discard losers** — recorded in episode `discarded[]` and workspace `DISCARDED` markers

Session model written to trajectory: `shared_workspace_subprocess` (M2). A future `long_lived_aura` single-process multi-eval is reserved but **not claimed** until it exists. Stable refs ≠ fiber-live FlatAST.

### aura-repo profile (M2)

Repos that look like Aura itself (`build.py`, tests) get `--profile aura-repo`:

- Detect: `--aura-ref` / `AURA_REF` / `/workspace/aura-grok`
- Fitness: `build.py` hook (cheap `list` by default) or simulated if GLIBCXX / toolchain broken
- Metrics: `compile_ms`, `incr_claimed`, **`incr_proven=false`** until storm-still-incr is proven
- Dogfood: cybrid-systems/aura (local `/workspace/aura-grok` when present)

Default CI stays `--mode simulated` (optionally with `--profile aura-repo --no-live-build`).

## Trajectory store

Append-only episodes (see [trajectory-protocol-v0.md](trajectory-protocol-v0.md)). Feeds RL export and specialist distillation. Off-runtime chat logs are **devalued** relative to on-runtime mutate/eval tapes.

## Evolving memory / harness

| Level | What | Production posture |
|-------|------|--------------------|
| **L1** | Strategy code (scout/mutate/eval policies as code) | First-class; mutate under canary |
| **L2** | Offline-trained weights | Promote after offline eval |
| **L3** | Online weights | **Experimental only** |

### M3 harness canary

`HarnessConfig` (`.aura-build/harness.json`) is a mutable L1 object:

- `worldline_count`, `fitness_weights`, `routing` (`simulated|aura|auto`)
- `aura-build harness-mutate --set …` → **propose** → canary episode on shadow profile → **commit|heal|discard**
- **AUTOPROMOTE default OFF** (`AURA_BUILD_AUTOPROMOTE` / `--autopropote`)
- Every change records `harness.mid` + `harness.actions[]` in the trajectory

Memory: `MemoryStore` under `.aura-build/memory/<profile>.json` (get/set via CLI or orch).

L2: `resolve_l2_weights(id)` stub only — no training, no tensor load.

Do **not** read a committed harness JSON or `stable_ref` as fiber-live FlatAST / proven incr.

## Anti-postman default

Prefer hot-object worldlines over git-worktree mail. If the system falls back to “clone, patch, PR” as the only path, architecture has regressed.
