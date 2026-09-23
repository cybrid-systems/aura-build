# aura-build

**EN:** Dev-time room on the Aura execution floor — hot FlatAST worldlines, fiber multi-candidate select-best, trajectory flywheel. Not another coding agent.

**中文：** Aura 执行层上的开发时「房间」——热 FlatAST 世界线、多候选选优、轨迹飞轮。不是又一款 coding agent。

## One-line pitch

Prefer live-object worldlines over git-worktree mail; dogfood [cybrid-systems/aura](https://github.com/cybrid-systems/aura); turn every mutate→eval→select into RL/specialist fuel.

一句话：用活对象世界线代替邮差式 worktree；狗粮 Aura；把每次 mutate→eval→select 变成 RL / 专才蒸馏燃料。

## Non-goals / 非目标

| Deny | Why |
|------|-----|
| Another coding agent / prettier language | Aura is the runtime; this is the room on the floor |
| Plugin-as-moat | Soft ≠ Restricted; integrations are soft surfaces |
| Git-worktree-as-primary | Anti-postman: mail is fallback, not the product |
| TUI/ACP-first | Headless/CI first (surface shape inspired by grok-build; product is not grok-build) |

## Docs

- [Narrative](docs/narrative.md) — 邮差 vs 活对象
- [Architecture](docs/architecture.md)
- [Trajectory protocol v0](docs/trajectory-protocol-v0.md)
- [Iteration plan](docs/iteration-plan.md) — M0–M5
- [Value](docs/value.md) · [Investor](docs/investor.md) · [Founders narrow path](docs/founders-narrow-path.md)


## Run

```bash
./scripts/smoke.sh          # simulated backend; creates .venv, pytest, one episode
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

## Status

**M3** — Self-evolving **memory / harness** at L1: mutable harness config, canary propose→commit|heal|discard, file-backed memory under `.aura-build/`, L2 stub by weights id. **AUTOPROMOTE default OFF**. Trajectories keep **`incr_proven=false`**. Not fiber-live.

**M2** — Worldline API (parent → N stable refs on shared workspace) + `--profile aura-repo` fitness hooks. Session model: `shared_workspace_subprocess`.

**M1** — `RuntimeBackend`: `SimulatedBackend` + `AuraBackend` (subprocess mutate:rebind + eval-current). Honest `runtime.mode`.

**Not yet (M4+):** RL export / specialist training notes; real L2 weight artifacts; fiber-live multi-worldline on one FlatAST; proven storm-still-incr (`incr_proven=true`); long-lived Aura multi-eval. Do not read `stable_ref` as live fibers.

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
