# aura-build

**EN:** Dev-time room on the Aura execution floor — hot FlatAST worldlines, fiber multi-candidate select-best, trajectory flywheel. Not another coding agent.

**中文：** Aura 执行层上的开发时「房间」——热 FlatAST 世界线、多候选选优、轨迹飞轮。不是又一款 coding agent。

## One-line pitch

Prefer live-object worldlines over git-worktree mail; dogfood [cybrid-systems/aura](https://github.com/cybrid-systems/aura); turn every mutate→eval→select into RL/specialist fuel.

一句话：用活对象世界线代替邮差式 worktree；狗粮 Aura；把每次 mutate→eval→select 变成 RL / 专才蒸馏燃料。

## Kernel = Aura (hard)

**Product core is written in Aura** under [`aura/`](aura/): orchestration, worldlines,
mutate/eval bridge, prove-incr / doctor honesty flags, harness L1 mutate+canary,
trajectory write, memory, ACP/TUI stubs, export JSON+redaction (`aura/main.aura` + modules).

Python is a **thin CLI host only**: argparse, `kernel.py` invoke Aura, Parquet
adapter, light schema for smoke/refuse messages, and a few host-side helpers
(`l2 promote --from-export` corpus gate, memory JSON I/O, prove *refuse* report).

**Python orch is gone.** Former reimplementations are **deleted** (not stubs); the CLI
refuses with `kernel=python_deprecated` when Aura is missing. There is **no** silent
CI green path that pretends Python is the product.

| Env / path | Role |
|------------|------|
| `AURA_BIN` + GCC16 libstdc++ sidecar | Required for orch CLIs (`run`, `harness-mutate`, `acp`, `tui`, …) |
| `AURA_BUILD_FORCE_PYTHON` | **Deprecated / debug-only** — disables Aura prefer so the host **refuses**; does **not** restore Python orch |
| Host without Aura | pytest host unit tests + `--help` + prove refuse report; orch episodes **skip** |

### Which CLIs are Aura-first

| CLI | When Aura healthy | Without Aura |
|-----|-------------------|--------------|
| `run` / `harness-mutate` / `pursue` / `acp` / `tui` / `harness-show` | **Aura kernel** | refuse (`kernel=python_deprecated`, exit 2) |
| `pursue` | **Aura kernel** | refuse (`kernel=python_deprecated`) |
| `prove-incr` | **Aura kernel** (measured storm) | honest refuse report only (no storm orch) |
| `doctor` | **Aura kernel** | host snapshot of last report / probe |
| `export` | **Aura kernel** JSON+redaction; Parquet via thin Python adapter | refuse (`kernel=python_deprecated`) — no host redaction |
| `memory` / `l2 show|list|promote` | Aura when healthy | thin host JSON I/O; `l2 promote --from-export` stays host corpus gate |

```bash
# Primary path (Aura kernel) — requires AURA_BIN + sidecar
export AURA_BIN=/workspace/aura-redis/.deps/aura/build/aura
./scripts/run-aura-kernel.sh          # AURA_BUILD_CMD=run by default
aura-build run --prompt "demo" --mode simulated   # CLI → Aura kernel
aura-build prove-incr --cycles 2 --worldlines 1
aura-build harness-mutate --prompt "canary" --set worldline_count=4
aura-build doctor
```

Honest flags: never fake `incr_proven` / `fiber_live` (env alone cannot elevate).
Trajectory / stdout show `kernel=aura` on the kernel path.

### Deleted / gutted Python modules

| Was | Now |
|-----|-----|
| `orch.py` / `worldline.py` / `profile_aura_repo.py` / `acp.py` / `tui.py` | **deleted** — product in `aura/*.aura`; CLI refuses via `deprecated.refuse` |
| `export.py` redaction / JSONL batch | **Parquet adapter only** — JSON+redaction in `aura/export.aura` |
| `prove_incr.py` storm loop | host refuse report only — product in `aura/prove.aura` |
| `harness.py` canary engine | `default_root` + `AUTOPROMOTE_ENV` only — product in `aura/harness.aura` |
| `runtime.py` SimulatedBackend / AuraBackend orch | probe + libstdc++ sidecar helpers for `kernel.py` only |

**Rough host LOC (excl. tests):** ~1.9k lines (`cli` ~360 dispatch + `cli_parser` ~200 flags; rest thin). Product logic LOC lives under `aura/` (~2k).

**Still in Python (host):** `cli.py` + `cli_parser.py`, `kernel.py`, `runtime.py` (probe + sidecar),
`export.py` (Parquet adapter only), light `schema.py` / `trajectory.py` (host smoke
gate), `l2_weights.py` (`promote --from-export` corpus gate), thin `memory.py` /
`harness.py` / `prove_incr.py` refuse helpers, `deprecated.py`.

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
./scripts/smoke.sh          # host pytest + refuse checks; Aura kernel episodes when AURA_BIN healthy
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
| **Post-M5** | `prove-incr` / `doctor`; fail-closed report; fiber probe; **auto-attach** on `run` | `incr_proven=true` only with measured incr-valid signal; fiber-live only after denseness probe (spawn+join + same-FlatAST multi); env alone cannot elevate |

**Beyond / deferred:** real L2 tensor/mmap (`stub=False`); fiber-live FlatAST (needs `AURA_BUILD_FIBER_SESSION_OK`); full TUI / editor ACP embed. Storm-still-incr is **proven** on healthy Aura via `compile:epoch` / `query:jit-stats-hash` deltas → `AURA_BUILD_INCR_VALID` (see [storm-still-incr.md](docs/storm-still-incr.md)); refuse when marker absent.

### TUI / ACP (M5)

```bash
# Stdlib status stub — Aura-first when AURA_BIN healthy (not a full-screen TUI)
aura-build tui
aura-build tui --json
# Without AURA_BIN: tui refuses (python_deprecated) — no fake status orch

# Agent control plane hooks — Aura-first when AURA_BIN healthy (headless remains SSOT)
aura-build acp hooks
aura-build acp start --prompt "dogfood session"
aura-build acp status          # honesty: incr_proven / fiber_live never faked
aura-build acp worldlines --traj trajectories/smoke.jsonl
aura-build acp worldlines --workspace /path/to/shared_ws
aura-build acp discard --workspace /path/to/shared_ws --ref wl-1
aura-build acp promote --id specialist.stub.v0 --notes "offline"
aura-build acp export --out trajectories/export.json
# AURA_BUILD_FORCE_PYTHON=1 refuses acp (deprecated; does not restore Python orch)
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



### Self-evolve (Post-M5++)

Dogfood mutate on **this** repo, materialize the winner, verify, then commit/push `main`:

```bash
# Requires AURA_BIN + sidecar. Dry run (no push):
aura-build self-evolve --prompt "dogfood aura-build" --no-push --verify smoke

# Materialize + verify only (no git):
aura-build self-evolve --prompt "dry" --no-commit --verify none

# Live: verify green ⇒ commit main + push origin main (skips CI wait)
aura-build self-evolve --prompt "ship" --verify smoke
```

Honesty: never invents `incr_proven` / `fiber_live`. Commit message carries traj id,
harness mid, and honesty flags. Without `AURA_BIN`, the command refuses.

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

### Fiber worldlines (slice 3)

When prove/doctor denseness says `fiber_live` (or the run-time probe succeeds),
orch fans out via `fiber:spawn` / same-FlatAST mutate and records
`runtime.worldline_backend=fiber_graph`. Otherwise file layout +
`worldline_backend=file`. Never fake; force file anytime:

```bash
aura-build run --prompt "fiber wl" --mode aura --worldlines 3
# look for: worldline_backend=fiber_graph  (when denseness live)
AURA_BUILD_WORLDLINE_BACKEND=file aura-build run --prompt "file wl" --mode aura --worldlines 3
# look for: worldline_backend=file
```

### Trajectory export (M4)

Aura-first when `AURA_BIN` + sidecar are healthy: the kernel writes the redacted JSON array (`aura/export.aura`). **Parquet is not produced in Aura**; the Python host optionally converts the JSON array → Parquet as a thin adapter when `pandas`+`pyarrow` are installed. Without Aura / with `AURA_BUILD_FORCE_PYTHON`, `export` **refuses** — no silent Python redaction path.


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

### Canary harness mutate demo (L1 = `std/hot-strategy`)

Live L1 uses Aura `hot-strategy:register!/swap!/heal!` when the kernel is healthy;
`harness.json` is the durable mirror. Trajectories record `l1_backend=hot-strategy|file`.
AUTOPROMOTE stays **OFF** by default (discard → heal live strategy).

```bash
# AUTOPROMOTE off (default): canary may pass; live L1 heal!s back; harness.json not committed
aura-build harness-mutate --prompt "demo canary" --seed 1 \
  --set worldline_count=4 --fitness-weight tests=0.8
# look for: l1_backend=hot-strategy outcome=discard

# Reject bad L1 before default path (exit 1, outcome=heal, still hot-strategy)
aura-build harness-mutate --prompt "bad L1" --set worldline_count=0

# Demo commit (explicit): env or flag — swap kept + harness.json mirrored
AURA_BUILD_AUTOPROMOTE=1 aura-build harness-mutate --prompt "promote demo" \
  --set routing=auto --set l2_weights_id=specialist.stub.v0
# or:  --autopropote

# Force file-only L1 (no hot-strategy swap); still honest about fiber_live/incr_proven
AURA_BUILD_L1_BACKEND=file aura-build harness-mutate --prompt "file L1" --set worldline_count=4

aura-build harness-show
aura-build doctor   # honesty includes l1_backend=
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




## pursue --goal (continuous transform)

First-class continuous goal loop owned by the **Aura kernel** (`aura/pursue.aura`).
Python only parses flags and invokes the kernel (same host path as `run` / `prove-incr`).

Workflow each round:

1. Doctor/prove honesty snapshot (refuse closed if Aura missing or backends incoherent)
2. Fan-out worldlines (`fiber_graph` when `fiber_live`, else `file`) + mutate:rebind / eval
3. `select-best`, discard losers, append trajectory
4. Optional MiniMax **hint only** (`--with-llm`) — never the loop controller
5. Optional one-shot `harness-mutate` canary (`--harness-mutate`, AUTOPROMOTE off)
6. Stop on `goal_met` | `max_rounds` | `honesty_fail`

Trajectory per-round fields: `goal`, `round_i`, `selected_id`, `fitness`,
`worldline_backend`, `fiber_live`, `incr_proven`, `l1_backend`, `stop_reason`.

```bash
export AURA_BIN=/workspace/aura-redis/.deps/aura/build/aura
# short smoke (2 rounds × 2 worldlines)
aura-build pursue --goal "demo select-best fitness" --max-rounds 2 --worldlines 2 \
  --mode aura --min-fitness 0.8 --json

# example honest lines (backends from probe, never env-faked):
# pursue honesty worldline_backend=fiber_graph fiber_live=True incr_proven=False l1_backend=hot-strategy
# pursue round=1/2 selected=wl-1 fitness=0.8854 worldline_backend=fiber_graph fiber_live=True stop_reason=continue
# pursue done goal_met=False stop_reason=max_rounds best_fitness=0.8854 worldline_backend=fiber_graph kernel=aura
```

Flags: `--goal` (required), `--predicate fitness_ge:N` / `--min-fitness`, `--max-rounds`,
`--worldlines`, `--mode aura|simulated|auto`, `--with-llm`, `--harness-mutate`, `--json`.

### MiniMax dogfood (Post-M5++)

Closed loop: **MiniMax-M3** proposes a small Aura program → Aura binary verify →
repair via worldlines select-best (host HTTP + Aura orch stamp). Prefer Aura
kernel product; Python host owns the OpenAI-compatible HTTP client only.

Secrets (never commit / never put in traj README):

| Path | Role |
|------|------|
| `~/.config/aura-build/minimax_api_key` | API key file (loaded into process env only) |
| `~/.config/aura-build/minimax.env` | `MINIMAX_BASE_URL`, `MINIMAX_MODEL`, `MINIMAX_API_KEY_FILE` |

Verified base URL for this dogfood: `https://api.minimaxi.com/v1` (model `MiniMax-M3`). **CN site only** — `api.minimax.io` is rejected/rewritten (401 for this key).
Set `AURA_BUILD_LLM=minimax` optionally; CLI profile is the `llm` / `llm-dogfood` commands.

```bash
# Thin chat (thinking disabled by default for speed)
export AURA_BIN=/workspace/aura-redis/.deps/aura/build/aura
aura-build llm --prompt "Reply with PONG" --json

# Closed loop: fib Aura program, up to 8 repair rounds, 3 worldlines
aura-build llm-dogfood --task fib --max-rounds 8 --worldlines 3 --json

# Tiny external project dogfood (examples/projects/mini-greet → GREET=aura)
aura-build llm-dogfood --task greet --max-rounds 8 --worldlines 3 --json
./examples/projects/mini-greet/verify.sh examples/projects/mini-greet/stub.aura  # expect fail

# Slightly harder: mini-calc → ADD=7 / MUL=12 / MIX=17 via define add/mul
aura-build llm-dogfood --task calc --max-rounds 8 --worldlines 3 \
  --out trajectories/mini_calc_dogfood.jsonl --json
./examples/projects/mini-calc/verify.sh examples/projects/mini-calc/stub.aura  # expect fail

# Harder still: mini-kv in-memory get/set (prefer --project over registry edits)
aura-build llm-dogfood --project examples/projects/mini-kv --max-rounds 8 \
  --worldlines 3 --out trajectories/mini_kv_dogfood.jsonl --json
# registry alias:
aura-build llm-dogfood --task kv --max-rounds 8 --worldlines 3 --json
./examples/projects/mini-kv/verify.sh examples/projects/mini-kv/stub.aura  # expect fail

# Multi-file (lib.aura + main.aura): mini-bank transfer / conservation
aura-build llm-dogfood --project examples/projects/mini-bank --max-rounds 12 \
  --worldlines 3 --out trajectories/mini_bank_dogfood.jsonl --json
./examples/projects/mini-bank/verify.sh examples/projects/mini-bank/stub  # expect fail

# Harder 3-file sticky router (table + match + main): exact + prefix + 405
aura-build llm-dogfood --project examples/projects/mini-router --max-rounds 12 \
  --worldlines 3 --out trajectories/mini_router_dogfood.jsonl --json
# registry alias:
aura-build llm-dogfood --task router --max-rounds 12 --worldlines 3 --json
./examples/projects/mini-router/verify.sh examples/projects/mini-router/stub  # expect fail
```

Tasks: `fib` (see `examples/minimax_fib_task.md`), `greet` (see
`examples/projects/mini-greet/`), `calc` (see `examples/projects/mini-calc/` —
named helpers + multi-line stdout), `kv` (see `examples/projects/mini-kv/` —
`kv-set`/`kv-get` + GET_a/GET_b/MISS/GET_c). Prefer
`llm-dogfood --project DIR` for new mini projects (`GOAL.md` + `stub.aura` +
`verify.sh` / `dogfood.json`) so the TASKS registry stays thin. MiniMax is
propose-only; project `verify.sh` (when present) is the fitness oracle;
worldlines select-best + repair. Honesty: `fiber_live` only when prove says so;
otherwise `session_model=shared_workspace_subprocess`. Trajectories record
`runtime.kernel=aura`, `runtime.llm.model`, `runtime.dogfood.task/project`,
actions/fitness; API keys are redacted.

### Dogfood lessons (mini-kv)

- **Friction → fix:** adding a fourth mini project required editing hard-coded
  `--task` choices + `TASKS` dict; shipped `--project` so any GOAL/verify dir
  dogfoods without a registry patch.
- **Friction → fix:** structure-fail traj notes were hard-coded to `add`/`mul`;
  now emit the actual `source_res` patterns (works for `kv-set`/`kv-get`).
- **Friction → fix:** project `verify.sh` was docs-only; `--project` / kv task
  now prefer it as the verify oracle and feed its stderr into repair.
- **Friction → fix:** `llm-dogfood --project …` still defaulted `--task fib`, so
  traj/`summary.task` lied as `fib` while verifying mini-kv; now project label
  wins unless the project was auto-loaded from an explicit registry `--task`.

### Dogfood lessons (mini-router / 3-file)

- **Friction → fix:** 2-file extract assumed lib+main; `extract_aura_sources` now
  keeps stable fence order for 3+ files, zips unnamed fences, and caps per-file /
  total bytes so runaway fences cannot blow the workspace.
- **Friction → fix:** repair always asked for ONE program; multi-file repair now
  requests named fences, highlights `verify mismatch line N:` stderr, and
  **merges omitted files from the previous candidate** (per-file repair) instead
  of resetting to stubs.
- **Friction → fix:** CLI listed `--task bank` without a TASKS entry; bank +
  router are thin registry aliases that auto-load `examples/projects/mini-*`.
- **Sticky stub lesson:** mini-router stubs break prefix (`GET_API_V1`/`V2`) and POST
  405 on purpose so MiniMax must fail→repair across table/match/main.
- **Friction → fix:** MiniMax often one-shot the 3-file router from the goal alone;
  `dogfood.json` `seed_from_stub: true` now verifies the sticky stub first and feeds
  that failure into round-0 repair so the closed loop exercises fail→repair.

### Self-evolve after external dogfood

Once mini projects like `mini-greet` / `mini-calc` verify green, aura-build can evolve **its own**
product code (still Aura-kernel + thin host):

```bash
# Dry / no-push smoke only — prefer after external dogfood is green
aura-build self-evolve --prompt "dry after mini-calc" --no-push --verify smoke
```

Do not push self-evolve unless verify is green and the diff is clearly product-useful.

## License

Apache-2.0
