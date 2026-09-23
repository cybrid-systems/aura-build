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

**M1** — `RuntimeBackend` protocol: `SimulatedBackend` + `AuraBackend` (subprocess mutate:rebind + eval-current). Trajectories set `runtime.mode` honestly. Default remains simulated.

**Not yet:** fiber-live multi-worldline on one FlatAST, aura-repo incr-compile fan-out — that is **M2**. Do not read M1 trajectories with `mode=simulated` as live worldlines; `mode=aura` is a short shell bridge, not full floor concurrency.

## License

Apache-2.0
