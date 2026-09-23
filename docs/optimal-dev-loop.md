# Optimal development loop (SSOT)

> **Kernel = Aura.** This doc is the north-star loop for aura-build.
> Code and README must aim here; cold subprocess verify is a **fallback**, not the product.

## Loop (one picture)

```
Long-lived Aura serve session (business / candidate loaded once)
  → predicate = real tests / in-session eval
  → aura-build fiber worldlines mutate → in-session eval → select-best
  → traj; LLM optional propose-only
  → promote winner; git publish only (escape hatch)
```

Anti-postman: prefer hot FlatAST / long-lived serve over “spawn aura, mail stdout, die” per candidate.

## Session model honesty (`runtime.session_model`)

| Value | When | Meaning |
|-------|------|---------|
| `serve` | Host-managed long-lived `aura --serve` attach is **alive** (pid + ping) | Primary dogfood verify path: reuse one process for N eval rounds |
| `fiber_denseness_in_process` | Denseness probe: `fiber:spawn`+join + same-FlatAST multi | In-process fiber graph worldlines |
| `shared_workspace_subprocess` | Neither of the above | File workspace + **cold** `aura` / `verify.sh` per candidate |

Never invent `serve` / `fiber_live` / `incr_proven` from env alone.
`AURA_BUILD_SESSION=1` (or a marker path) only **requests** attach; doctor/`serve_session_ok` require a live process.

### Related honesty fields

| Field | Meaning |
|-------|---------|
| `serve_session_ok` | True if host serve attach is alive **or** (when available) `--serve-async-bench` child probe passes |
| `serve_cross_session_shared_ast` | True only when orch + project share one FlatAST across sessions — **still deferred** |
| `fiber_live` | Denseness only; env cannot elevate |
| `incr_proven` | Measured storm-still-incr only |

## Roles

| Layer | Owns |
|-------|------|
| **Aura `--serve` (long-lived)** | Compile/eval floor; set-code → eval-current; multi-round without cold start |
| **aura-build kernel (`aura/*.aura`)** | Worldlines, select-best, prove/doctor honesty, traj stamp |
| **Thin Python host** | CLI, manage serve PID/marker, MiniMax HTTP propose-only, Parquet adapter |
| **LLM** | Propose / repair **hints only** — never the loop controller |
| **Git** | Publish escape hatch after promote; not the concurrency model |

## How to run (box)

```bash
export AURA_BIN=/workspace/aura-redis/.deps/aura/build/aura   # + GCC16 sidecar as elsewhere

# 1) Start long-lived serve (writes .aura-build/serve-session.json)
aura-build session start
aura-build session status          # serve_attach_ok / session_model=serve
aura-build doctor                  # serve_session_ok when attach live

# 2) In-session dogfood (no MiniMax required) — closed loop on serve path
aura-build session dogfood --rounds 3 --json

# 3) Optional: MiniMax propose-only; verify prefers live session for single-file tasks
aura-build llm-dogfood --task greet --max-rounds 4 --worldlines 2 --json

aura-build session stop
```

Cold subprocess verify remains when session is down (`session_model=shared_workspace_subprocess`,
`via=aura_bin|verify_script`).

## What is still deferred

1. **True `--serve-async` multi-worker** on Soft boxes (production Ready self-check refuses Soft multi-worker). MVP uses long-lived `--serve` (stdin JSON-line / expr protocol).
2. **Shared FlatAST across aura-build orch + project** (`serve_cross_session_shared_ast=true`) — attach today is host-managed process reuse for verify/eval, not one FlatAST shared with fiber orch.
3. Fiber worldlines *mutating* the same serve session’s AST as the project under test (orch still denseness/`file` as today).
4. JSON-RPC “postman” as a primary surface — denied; serve stdin is the attach, not a new product.

## Demoted: mini-* llm-dogfood toys

`examples/projects/mini-*` + `llm-dogfood --task {fib,greet,calc,kv,…}` are **CI fixtures / regression**
for propose→verify→repair plumbing. They are **not** the primary workflow.

Primary workflow = this loop: long-lived serve → in-session predicate → worldlines → traj → git publish.

## See also

- [architecture.md](architecture.md) — layers
- [storm-still-incr.md](storm-still-incr.md) — prove-or-refuse
- [trajectory-protocol-v0.md](trajectory-protocol-v0.md) — `runtime.session_model`
- [iteration-plan.md](iteration-plan.md) — deferred checklist
