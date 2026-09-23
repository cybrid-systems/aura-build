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
2. **Mutate** — propose N worldline mutations (Aura mutate API; M0 simulates).
3. **Eval** — fitness: tests, incr-compile cost, audit constraints.
4. **Select-best** — collapse to one worldline; append trajectory.

### Worldlines

A worldline is a **candidate live-object history**, not a git worktree. Default is anti-postman: keep candidates on the floor with stable IDs. Git/mail export is an escape hatch for humans and external CI, not the primary concurrency model.

### aura-repo profile

Repos that look like Aura itself (`build.py`, tests, incr compile) get a first-class profile: multi-candidate mutate under incremental compile, select-best by test+cost fitness. Dogfood: cybrid-systems/aura (and local refs like `/workspace/aura-grok` when present).

## Trajectory store

Append-only episodes (see [trajectory-protocol-v0.md](trajectory-protocol-v0.md)). Feeds RL export and specialist distillation. Off-runtime chat logs are **devalued** relative to on-runtime mutate/eval tapes.

## Evolving memory / harness

| Level | What | Production posture |
|-------|------|--------------------|
| **L1** | Strategy code (scout/mutate/eval policies as code) | First-class; mutate under canary |
| **L2** | Offline-trained weights | Promote after offline eval |
| **L3** | Online weights | **Experimental only** |

## Anti-postman default

Prefer hot-object worldlines over git-worktree mail. If the system falls back to “clone, patch, PR” as the only path, architecture has regressed.
