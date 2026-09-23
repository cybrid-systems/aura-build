# aura-build

**EN:** Dev-time room on the Aura execution floor — hot FlatAST worldlines, fiber multi-candidate select-best, trajectory flywheel. Not another coding agent.

**中文：** Aura 执行层上的开发时「房间」——热 FlatAST 世界线、多候选选优、轨迹飞轮。不是又一款 coding agent。

## One-line pitch

Prefer live-object worldlines over git-worktree mail; dogfood [cybrid-systems/aura](https://github.com/cybrid-systems/aura); turn every mutate→eval→select into RL/specialist fuel.

一句话：用活对象世界线代替邮差式 worktree；狗粮 Aura；把每次 mutate→eval→select 变成 RL / 专才蒸馏燃料。

## Kernel = Aura (hard)

**Product core is written in Aura** under [`aura/`](aura/): orchestration, worldlines,
mutate/eval bridge, prove-incr / doctor honesty flags, harness L1 mutate+canary,
trajectory write, memory, L2 stub metadata (`aura/main.aura` + modules).

Python is a **thin CLI / test harness** that shells out to the `aura` binary
(with the GCC16 libstdc++ sidecar). It still owns the TUI status stub, optional Parquet conversion for export, schema
validation, and a **CI-safe fallback** when no Aura binary is present
(`AURA_BUILD_FORCE_PYTHON=1` forces the fallback). ACP prefers the Aura kernel.

### Which CLIs are Aura-first

| CLI | When Aura healthy | Python |
|-----|-------------------|--------|
| `run` | **Aura kernel** (`orch.aura`); traj `runtime.kernel=aura` | CI fallback / `--json` |
| `prove-incr` | **Aura kernel** (`prove.aura` in-process storm) | fail-closed refuse report |
| `harness-mutate` | **Aura kernel** (`harness.aura` + canary); `kernel=aura` | CI fallback / `--json` |
| `doctor` / `harness-show` | **Aura kernel** (cheap) | fallback |
| `memory` / `l2 show\|list\|promote` | Aura when healthy (promote `--from-export` stays Python) | fallback |
| `export` | **Aura kernel** (JSON array + default-ON redaction); Parquet via thin Python adapter | `AURA_BUILD_FORCE_PYTHON=1` / no binary |
| `acp` | **Aura kernel** (`acp.aura` hooks: start/status/worldlines/promote/discard/export) | `AURA_BUILD_FORCE_PYTHON=1` / no binary |
| `tui` | — | **Python stub** (may reuse ACP status) |

```bash
# Primary path (Aura kernel) — requires AURA_BIN + sidecar
export AURA_BIN=/workspace/aura-redis/.deps/aura/build/aura
./scripts/run-aura-kernel.sh          # AURA_BUILD_CMD=run by default
aura-build run --prompt "demo" --mode simulated   # CLI → Aura kernel when healthy
aura-build prove-incr --cycles 2 --worldlines 1
aura-build harness-mutate --prompt "canary" --set worldline_count=4
aura-build doctor
```

Honest flags: never fake `incr_proven` / `fiber_live` (env alone cannot elevate).
Trajectory / stdout show `kernel=aura` on the kernel path (`kernel=python` on fallback).

## Non-goals / 非目标

| Deny | Why |
|------|-----|
| Another coding agent / prettier language | Aura is the runtime; this is the room on the floor |
| Plugin-as-moat | Soft ≠ Restricted; integrations are soft surfaces |
| Git-worktree-as-primary | Anti-postman: mail is fallback, not the product |
| TUI/ACP-as-product | Headless/CI first (surface *shape* inspired by grok-build; product is not grok-build) |

## Docs

- [Narrative](docs/narrative.md) — 邮差 vs 活对象
- [Architecture](docs/architecture.md)
- [Trajectory protocol v0](docs/trajectory-protocol-v0.md)
- [Specialist training notes](docs/specialist-training-notes.md) — M4/M5 export + L2 metadata
- [Iteration plan](docs/iteration-plan.md) — M0–M5 + Post-M5 status table
- [Storm-still-incr](docs/storm-still-incr.md) — prove-or-refuse harness
- [Value](docs/value.md) · [Investor](docs/investor.md) · [Founders narrow path](docs/founders-narrow-path.md)

## Run

```bash
./scripts/smoke.sh          # pytest (Python fallback) + Aura kernel episode when AURA_BIN healthy
# or manually:
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
aura-build run --prompt "demo select-best" --mode simulated
```

### Runtime modes

| Flag | Behavior |
|------|----------|
| `--mode simulated` (default) | Deterministic fake worldlines; CI-safe |
| `--mode aura` | Shell to Aura binary (`--aura-bin` / `AURA_BIN`); **fails closed** if missing/broken |
| `--mode auto` | Use Aura when probe succeeds, else simulated; trajectory `runtime.mode` is honest |

Optional live smoke (skips cleanly if Aura unavailable):

```bash
export AURA_BIN=/path/to/build/aura   # e.g. /workspace/aura-grok/build/aura
./scripts/aura_smoke.sh
```

Writes validated episode JSONL under `trajectories/` (gitignored). Sample shape in `examples/`.

## Status (M0–M5 + Post-M5)

| M | What works | What's stub / refused |
|---|------------|------------------------|
| **M0** | `run`, trajectory JSONL, simulated select-best, pytest smoke | — |
| **M1** | `RuntimeBackend` simulated + Aura subprocess bridge; honest `runtime.mode` | Not fiber-live multi-worldline |
| **M2** | Shared workspace stable refs, aura-repo profile, discard losers | `incr_proven=false`; stable_ref ≠ fibers |
| **M3** | Harness canary (AUTOPROMOTE OFF), memory store, L2 id stub | No L2 tensors; no online L3 |
| **M4** | `export` JSON (+ optional Parquet), privacy redaction default ON | No training loop |
| **M5** | `tui` status stub; `acp` hooks; L2 metadata load/promote under `.aura-build/weights/` | TUI ≠ full Textual; `stub=True` always (metadata only); no fiber-live / no `incr_proven=true` / no online L3 |
| **Post-M5** | `prove-incr` / `doctor`; fail-closed report; fiber probe; **auto-attach** on `run` | `incr_proven=true` only with measured incr-valid signal; fiber-live only with session OK; env alone cannot elevate |

**Beyond / deferred:** real L2 tensor/mmap (`stub=False`); fiber-live FlatAST (needs `AURA_BUILD_FIBER_SESSION_OK`); full TUI / editor ACP embed. Storm-still-incr is **proven** on healthy Aura via `compile:epoch` / `query:jit-stats-hash` deltas → `AURA_BUILD_INCR_VALID` (see [storm-still-incr.md](docs/storm-still-incr.md)); refuse when marker absent.

### TUI / ACP (M5)

```bash
# Stdlib status stub — session + last traj path (not a full-screen TUI)
aura-build tui
aura-build tui --json

# Agent control plane hooks — Aura-first when AURA_BIN healthy (headless remains SSOT)
aura-build acp hooks
aura-build acp start --prompt "dogfood session"
aura-build acp status          # honesty: incr_proven / fiber_live never faked
aura-build acp worldlines --traj trajectories/smoke.jsonl
aura-build acp worldlines --workspace /path/to/shared_ws
aura-build acp discard --workspace /path/to/shared_ws --ref wl-1
aura-build acp promote --id specialist.stub.v0 --notes "offline"
aura-build acp export --out trajectories/export.json
# Force Python fallback:
AURA_BUILD_FORCE_PYTHON=1 aura-build acp status
```

### L2 offline metadata (M5)

```bash
# Promote metadata-only stub (id, created, notes) — refuses l3_online=true corpora
aura-build l2 promote --id specialist.stub.v0 --notes "offline demo"
aura-build l2 promote --id specialist.from.export.v0 \
  --from-export trajectories/export.json --notes "gated"

aura-build l2 show --id specialist.stub.v0
aura-build l2 list

# Episode resolve picks up .aura-build/weights/<id>.json when present
aura-build run --prompt "with l2" --l2-weights-id specialist.stub.v0 --mode simulated
```

Example artifact shape: `examples/weights.specialist.stub.v0.json` → copy to `.aura-build/weights/specialist.stub.v0.json`.
**No training. No tensor load. `stub=True` until real bytes exist.**


### Prove-incr / doctor (Post-M5)

```bash
# Fail-closed if Aura missing/GLIBCXX; never lies about incr_proven
aura-build prove-incr
aura-build prove-incr --cycles 8 --worldlines 3 --json
./scripts/prove_incr.sh

aura-build doctor
aura-build doctor --json

# Episodes auto-attach prove honesty into traj runtime (default ON)
aura-build run --prompt "dogfood" --mode simulated
aura-build run --prompt "skip attach" --no-attach-prove --mode simulated
```

Report: `.aura-build/prove-incr-latest.json`. Trajectories carry
`runtime.prove_incr` (`incr_proven` / `measured` / `fiber_live` /
`session_model` / `reason`) — still **false by default**. Env
`AURA_BUILD_INCR_VALID=1` alone cannot force true. See
[storm-still-incr.md](docs/storm-still-incr.md).

### Trajectory export (M4)

Aura-first when `AURA_BIN` + sidecar are healthy: the kernel writes the redacted JSON array (`aura/export.aura`). **Parquet is not produced in Aura** (no clean in-kernel parquet writer); the Python host optionally converts the JSON array → Parquet as a thin adapter when `pandas`+`pyarrow` are installed. Set `AURA_BUILD_FORCE_PYTHON=1` to force the pure-Python exporter.


```bash
# Redacted JSON array (default). Parquet if pandas+pyarrow installed.
aura-build export --out trajectories/export.json

# From explicit dirs/files
aura-build export trajectories/ .aura-build/trajectories/ \
  --out /tmp/aura-export.json --parquet /tmp/aura-export.parquet

# Local dogfood only — keep raw paths/secrets
aura-build export --include-raw --out trajectories/export.raw.json

# Optional deps for Parquet
pip install 'aura-build[export]'
```

See [specialist-training-notes.md](docs/specialist-training-notes.md).

### Canary harness mutate demo

```bash
# AUTOPROMOTE off (default): canary may pass, but live harness is discarded (not committed)
aura-build harness-mutate --prompt "demo canary" --seed 1 \
  --set worldline_count=4 --fitness-weight tests=0.8

# Reject bad L1 before default path (exit 1, outcome=heal)
aura-build harness-mutate --prompt "bad L1" --set worldline_count=0

# Demo commit (explicit): env or flag
AURA_BUILD_AUTOPROMOTE=1 aura-build harness-mutate --prompt "promote demo" \
  --set routing=auto --set l2_weights_id=specialist.stub.v0
# or:  --autopropote

aura-build harness-show
aura-build memory set --profile default --key note --value "anti-postman"
aura-build memory get --profile default --key note
```

### aura-repo profile

```bash
# Detects AURA_REF or /workspace/aura-grok when build.py exists
aura-build run --prompt "dogfood select-best" --profile aura-repo \
  --aura-ref /workspace/aura-grok --mode simulated --worldlines 3

# Force simulated fitness (skip build.py hook) — CI-safe
aura-build run --prompt "ci" --profile aura-repo --no-live-build --mode simulated
```

## License

Apache-2.0
