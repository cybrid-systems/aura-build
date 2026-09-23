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
| `serve_mode` | `async` only after measured Soft Ready self-check for `--serve-async`; else `sync` (`--serve`). Soft (#3098) refuses async on this box → `sync` |
| `serve_cross_session_shared_ast` | True **only** when two named Aura serve sessions share one FlatAST (measured). Soft `--serve` uses separate CompilerService maps → **false**; env cannot elevate |
| `serve_same_session_mutate_ok` | Measured same-session `mutate:rebind` + `eval-current` on the holder serve process |
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
aura-build session status          # serve_attach_ok / serve_mode / shared_ast honesty
aura-build doctor                  # serve_session_ok when attach live

# 2) In-session dogfood (no MiniMax required) — closed loop on serve path
aura-build session dogfood --rounds 3 --json   # cold_spawns=0; path_kind=mutate_rebind when measured

# 3) Pursue on same-session mutate:rebind (default --prefer-session)
aura-build pursue --goal "emit GREET=aura" --min-fitness 0.8 --max-rounds 2 --worldlines 3 --json
# → worldline_backend=serve_mutate_rebind path_kind=mutate_rebind cold_spawns=0
# Soft Ready still refused (fail_bits=0x10); serve_mode=sync honest

# 4) Optional: MiniMax propose-only; verify prefers live session for single-file tasks
aura-build llm-dogfood --task greet --max-rounds 4 --worldlines 2 --json

aura-build session stop
```

Cold subprocess verify remains when session is down (`session_model=shared_workspace_subprocess`,
`via=aura_bin|verify_script`).

## What is still deferred / next gate

Precise Soft Ready diagnosis (fail bit map + why aura-build cannot clear it):
**[soft-ready-gate.md](soft-ready-gate.md)**.

1. **Soft Ready `--serve-async`** — measured refuse: Soft (`AURA_SANDBOX=off`) aborts with `#3098` `fail_bits=0x10` = bit4 `defaults_missing_soft` only (not ABI markers). Holder prefers async only after Soft Ready self-check; today it honestly falls back to `serve_mode=sync` (`aura --serve`). **Blocker is Aura runtime**, not a missing env flag — never flip sandbox to fake Ready.
2. **`serve_cross_session_shared_ast=true`** — Soft `--serve` named sessions do **not** share FlatAST (binding defined in `orch` is unbound in `project`). Real cross-session sharing ships with Soft-Ready `--serve-async` `shared_workspace_tree`. Same-session `mutate:rebind` **is** measured (`serve_same_session_mutate_ok`) and used by `session dogfood` + **`pursue` (default `--prefer-session`)** → `worldline_backend=serve_mutate_rebind`, `cold_spawns=0`.
3. Fiber orch worldlines *and* project-under-test as two named sessions on one shared tree (depends on gate 1–2).
4. JSON-RPC “postman” as a primary surface — denied; serve stdin / sock is the attach, not a new product.

## Demoted: mini-* llm-dogfood toys

`examples/projects/mini-*` + `llm-dogfood --task {fib,greet,calc,kv,…}` are **CI fixtures / regression**
for propose→verify→repair plumbing. They are **not** the primary workflow.

Primary workflow = this loop: long-lived serve → in-session predicate → worldlines → traj → git publish.

## See also

- [architecture.md](architecture.md) — layers
- [storm-still-incr.md](storm-still-incr.md) — prove-or-refuse
- [trajectory-protocol-v0.md](trajectory-protocol-v0.md) — `runtime.session_model`
- [iteration-plan.md](iteration-plan.md) — deferred checklist
