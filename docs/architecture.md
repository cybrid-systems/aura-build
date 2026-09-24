# Architecture

## Layers

```
┌─────────────────────────────────────────────────────────┐
│  Host (thin)                                            │
│  CLI / CI / TUI·ACP stub — no business moat here        │
└──────────────────────────┬──────────────────────────────┘
                           │ prompts, policy, I/O
┌──────────────────────────▼──────────────────────────────┐
│  Aura kernel (aura/*.aura) — PRODUCT CORE               │
│  scout → mutate → eval → select-best                    │
│  worldline fan-out · prove-incr · harness · traj        │
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

The host process is a **thin** adapter: argparse/CI entrypoints that **shell out to the Aura kernel** (`aura/main.aura`), plus export Parquet adapter and a few host JSON helpers. Product value lives in `aura/*.aura`. **Python orch was removed** — without Aura the host refuses (`kernel=python_deprecated`) or skips; `AURA_BUILD_FORCE_PYTHON` is deprecated and does not restore orch. Soft ≠ Restricted; deny plugin-as-moat.

## Aura control

The **Aura kernel** (`aura/orch.aura`, entered via `aura/main.aura`) owns the episode loop:

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

`WorldlineWorkspace` (Aura: `aura/worldline.aura`):

1. Snapshot **parent** under a shared workspace dir
2. Fork **N candidates** with `stable_ref` + `parent_id`
3. Eval each (profile fitness / backend)
4. **Discard losers** — recorded in episode `discarded[]` and workspace `DISCARDED` markers

Session model: `serve` (host long-lived `aura --serve` attach), `fiber_denseness_in_process` (denseness), or `shared_workspace_subprocess` (cold/file). Trajectory records `runtime.worldline_backend=fiber_graph|file`. Soft Ready `--serve-async` measured refuse on Soft (`serve_mode=sync`); `serve_cross_session_shared_ast` stays false until named sessions share FlatAST; same-session mutate measured. Env alone cannot elevate `fiber_live` / `serve` / shared_ast. SSOT: [optimal-dev-loop.md](optimal-dev-loop.md); Soft Ready: [soft-ready-gate.md](soft-ready-gate.md).

### aura-repo profile (M2)

Repos that look like Aura itself (`build.py`, tests) get `--profile aura-repo`:

- Detect: `--aura-ref` / `AURA_REF` / `/workspace/aura-grok`
- Fitness: `build.py` hook (cheap `list` by default) or simulated if GLIBCXX / toolchain broken
- Metrics: `compile_ms`, `incr_claimed`, **`incr_proven=false`** until storm-still-incr is proven; `run` auto-attaches prove honesty (`runtime.prove_incr`) but never invents true (env alone cannot elevate)
- Dogfood: cybrid-systems/aura (local `/workspace/aura-grok` when present)

Default CI stays `--mode simulated` (optionally with `--profile aura-repo --no-live-build`).

## Trajectory store

Append-only episodes (see [trajectory-protocol-v0.md](trajectory-protocol-v0.md)). Feeds RL export and specialist distillation. Off-runtime chat logs are **devalued** relative to on-runtime mutate/eval tapes.

### M4 batch export

`aura-build export` reads JSONL under `trajectories/` and `.aura-build/**`, validates `trajectory.v0`, applies privacy filters (**default ON**), writes a **JSON array**, and attempts **Parquet** when `pandas`+`pyarrow` are installed (optional extra `aura-build[export]`; otherwise clear skip message). `--include-raw` disables redaction for local dogfood only. Export is offline — no L3 weight updates. Field guide: [specialist-training-notes.md](specialist-training-notes.md).

## Evolving memory / harness

| Level | What | Production posture |
|-------|------|--------------------|
| **L1** | Strategy code (scout/mutate/eval policies as code) | First-class; mutate under canary |
| **L2** | Offline-trained weights | Promote after offline eval |
| **L3** | Online weights | **Experimental only** |

### M3 harness canary (L1 → `std/hot-strategy`)

`HarnessConfig` (`.aura-build/harness.json`) is the **durable mirror / config seed**.
Live L1 mutates through Aura `std/hot-strategy` when the kernel is healthy:

- `worldline_count`, `fitness_weights`, `routing` (`simulated|aura|auto`)
- `aura-build harness-mutate --set …` → **propose** → `hot-strategy:register!/swap!` → canary → **commit|heal|discard**
  - canary fail or AUTOPROMOTE off → `hot-strategy:heal!` (last-good)
  - commit → keep swap + write `harness.json` mirror
- **AUTOPROMOTE default OFF** (`AURA_BUILD_AUTOPROMOTE` / `--autopropote`)
- Trajectory records `harness.mid`, `harness.actions[]`, and honest `harness.l1_backend` (`hot-strategy`|`file`)
- Override: `AURA_BUILD_L1_BACKEND=file` forces file-only path (still no fake `fiber_live` / `incr_proven`)
- Fiber denseness probed honestly in prove/doctor; when `fiber_live`, orch/worldline fan-out via `fiber:spawn` (`worldline_backend=fiber_graph`); else file `parent/candidates/wl-N` (`worldline_backend=file`). Force file: `AURA_BUILD_WORLDLINE_BACKEND=file`.

Memory: `MemoryStore` under `.aura-build/memory/<profile>.json` (get/set via CLI or orch).

L2 (M5): `resolve_l2_weights(id, root=…)` loads **metadata-only** stubs from
`.aura-build/weights/<id>.json` (`id`, `created`, `notes`). Offline promote via
`aura-build l2 promote` (refuses `l3_online=true` corpora). Always `stub=True`
until real weight bytes exist — no training, no tensor/mmap, no online L3.

### M5 TUI / ACP

- `aura-build tui` — stdlib status printer (session + last traj); not a full TUI
- `aura-build acp {hooks,start,status,worldlines,promote,discard,export}` — Aura-first control
  plane wired to session marker, worldline workspace, L2 promote, and export
- Headless `run` / `export` / harness canary remain SSOT

Do **not** read a committed harness JSON, L2 metadata file, or `stable_ref` as
fiber-live FlatAST / proven incr / real specialist weights in memory.

## Optimal loop

See [optimal-dev-loop.md](optimal-dev-loop.md): long-lived serve → in-session eval → worldlines → traj; LLM propose-only; git publish escape hatch. `aura-build session start|status|stop|dogfood`.

## Anti-postman default

Prefer hot-object worldlines over git-worktree mail. If the system falls back to “clone, patch, PR” as the only path, architecture has regressed.

### Post-M5 prove-incr / doctor

`aura-build prove-incr` measures storm-still-incr or **refuses** (fail-closed on
GLIBCXX / missing binary). `aura-build doctor` aggregates probe + last report.
Session model stays `shared_workspace_subprocess` unless a fiber session marker
is observed. Details: [storm-still-incr.md](storm-still-incr.md).



## What Python still does

| Surface | Role |
|---------|------|
| `cli.py` + `cli_parser.py` + `kernel.py` | Argparse → env → `aura aura/main.aura`; refuse when unavailable |
| `export.py` | Parquet adapter only (JSON+redaction in `aura/export.aura`) |
| `l2_weights.py` / thin `memory.py` | Host metadata I/O; `l2 promote --from-export` corpus gate |
| `prove_incr.py` refuse helper | Honest fail-closed report only (no storm orch) |
| `runtime.py` | Binary probe + GCC16 libstdc++ sidecar for `kernel.py` |
| `orch.py` / `worldline.py` / `acp.py` / `tui.py` / … | **Deleted** — CLI refuses via `deprecated.py` |

**Aura-first CLIs** (require kernel when doing orch): `run`, `prove-incr`,
`harness-mutate`, `doctor`, `harness-show`, `acp`, `tui`, `export` (JSON), `memory`/`l2`
(Aura when healthy). Trajectories record `runtime.kernel=aura`. Never invent
`incr_proven` / `fiber_live`. Do not grow Python orch as the product.


## Self-evolve (Post-M5++)

**Combat SSOT:** [self-evolve-combat.md](self-evolve-combat.md) — Soft session + fiber
explore + fiber LLM + worldlines + dual sink (aura-build self-improve **and**
Aura/stdlib issues). That is the path that combines live capabilities; do not
claim stamp `self-evolve` is fiber-live.

### Stamp path (L1 / simulated fitness — not combat)

`aura-build self-evolve` is Aura-kernel-first:

1. Kernel (`aura/self_evolve.aura`) dogfoods harness L1 canary + worldline select-best
   over this repo, materializes `aura/self_evolve_stamp.aura`, writes traj with
   `runtime.kernel=aura` and honest `incr_proven` / `fiber_live`.
2. Host runs optional heavier verify (`--verify smoke|prove|kernel`).
3. On green: host commits on `main` (message carries traj id / harness mid / honesty)
   and pushes `origin main` unless `--no-push`.

Fail-closed: verify red or kernel `ok=false` ⇒ no commit/push. Python without
`AURA_BIN` refuses (`kernel=python_deprecated`).

Stamp path remains useful for L1 canary / commit-edge dogfood. **Combat** (Soft
Ready attach → fiber explore → dual sink) is the new SSOT for self-evolution;
see phases P0–P3 in [self-evolve-combat.md](self-evolve-combat.md).
