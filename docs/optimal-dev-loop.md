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
| `serve_mode` | `async` only after measured Soft Ready self-check for `--serve-async` (#4047 Soft Ready profile); else `sync` (`--serve`). Env cannot elevate |
| `serve_cross_session_shared_ast` | True **only** when two named Aura serve sessions share one FlatAST (measured on-proc / Soft Ready async). Soft sync `--serve` separate maps → **false**; env cannot elevate |
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
# Soft Ready tip (#4047): serve_mode=async + serve_cross_session_shared_ast=true when measured

# 4) Optional: MiniMax propose-only; verify prefers live session for single-file tasks
aura-build llm-dogfood --task greet --max-rounds 4 --worldlines 2 --json

aura-build session stop
```

Cold subprocess verify remains when session is down (`session_model=shared_workspace_subprocess`,
`via=aura_bin|verify_script`).

## What is still deferred / next gate

Precise Soft Ready diagnosis (fail bit map + why aura-build cannot clear it):
**[soft-ready-gate.md](soft-ready-gate.md)**.

1. **Soft Ready `--serve-async`** — on Aura tip with Soft Ready profile (#4047), Soft boxes (`AURA_SANDBOX=off`) measure `serve_mode=async` after honest self-check (`soft_ready_profile_4047`). Older tips without #4047 still refuse (`#3098` `fail_bits=0x10`) and fall back to `serve_mode=sync`. **Never env-fake** Soft Ready / async.
2. **`serve_cross_session_shared_ast=true`** — stamped only when measured (Soft Ready async on-proc orch→project / `shared_workspace_tree`). Soft sync `--serve` still keeps separate CompilerService maps → **false**. Same-session `mutate:rebind` remains measured and used by `session dogfood` + **`pursue` / `llm-dogfood --prefer-session`** → `worldline_backend=serve_mutate_rebind`, `cold_spawns=0` when attach live.
3. Fiber orch worldlines *and* project-under-test as two named sessions on one shared tree (works when 1–2 measure true; denseness fiber probe still optional / skippable via `AURA_BUILD_NO_FIBER_PROBE=1`).
4. JSON-RPC “postman” as a primary surface — denied; serve stdin / sock is the attach, not a new product.

## Demoted: mini-* llm-dogfood toys

`examples/projects/mini-*` + `llm-dogfood --task {fib,greet,calc,kv,stack,bank,router,cache,queue,pubsub,2pc,twopc,saga,…}` are **CI fixtures / regression**
for propose→verify→repair plumbing. They are **not** the primary workflow.

Primary workflow = this loop: long-lived serve → in-session predicate → worldlines → traj → git publish.


## Multi-file hot session verify + fiber explore

- **Hot verify:** when `prefer-session` and a live Soft serve attach exists, multi-file
  candidates are concatenated in `files` order and scored via session `set-code` +
  `eval-current` (`via=serve_session`, `cold_spawns=0`). Project `verify.sh` is an
  optional oracle / fallback — never invent a green. Structural `source_res` checks
  stay in Python (no cold aura spawn).
- **Fiber explore:** `--fiber-explore N` (default = `--worldlines`) fans out N explorer
  worldlines. Stamp `worldline_backend=fiber_graph` **only** when `fiber:spawn` denseness
  actually ran on the live serve FlatAST. Soft Ready `--serve-async` denseness is live
  after Aura [#4048](https://github.com/cybrid-systems/aura/issues/4048) (affinity +
  body mutex + Soft Ready auto workers=1) — probe on sync **and** async Soft Ready.
  Never invent `fiber_graph` without an ok probe; on probe failure keep
  `explore_parallel=host_thread` (honest).

- **Tools ≠ agents:** `--explore-tools rule,llm,intent` lists strategies any explorer
  may use (deterministic patch, MiniMax propose, intent skeleton). Stamp
  `tools_used` per worldline. There is no three-agent product taxonomy.

```bash
aura-build llm-dogfood --project examples/projects/mini-cache \
  --fiber-explore 3 --explore-tools rule,llm,intent --prefer-session \
  --max-rounds 8 --worldlines 3 --out trajectories/mini_cache_fiber_explore.jsonl --json

aura-build llm-dogfood --project examples/projects/mini-queue \
  --fiber-explore 3 --explore-tools rule,llm,intent --prefer-session \
  --max-rounds 16 --worldlines 3 --out trajectories/mini_queue_dogfood.jsonl --json

aura-build llm-dogfood --project examples/projects/mini-pubsub \
  --prefer-session --fiber-explore 3 --worldlines 3 \
  --max-rounds 16 --out trajectories/mini_pubsub_dogfood.jsonl --json

# Magnitude jump: 7-file two-phase commit (log+parts+vote+coord+recover+main)
aura-build llm-dogfood --project examples/projects/mini-2pc \
  --prefer-session --fiber-explore 3 --worldlines 3 --max-rounds 20 \
  --out trajectories/mini_2pc_dogfood.jsonl --json

# Order-of-magnitude harder: 10-file saga (idemp+journal+book+pay+ship+step+compensate+saga+query+main)
aura-build llm-dogfood --project examples/projects/mini-saga \
  --prefer-session --fiber-explore 3 --worldlines 3 --max-rounds 24 \
  --out trajectories/mini_saga_dogfood.jsonl --json
```


## Concurrent LLM explorers + Soft orch observation

Force N explorers to MiniMax-only (no rule/intent stealing the round) and stamp
Soft orch facade stats measured on the live serve session:

```bash
aura-build llm-dogfood --project examples/projects/mini-cache \
  --prefer-session --fiber-explore 3 --explore-tools llm \
  --concurrent-llm --max-rounds 8 --worldlines 3 --json
```

Honesty:
- `explore_parallel=fiber_graph` only when Soft denseness probe ok; else `host_thread`
- Default MiniMax propose is host HTTP → `llm_via=host` / `llm_parallel=host_thread`
- Optional `--fiber-llm` / `AURA_BUILD_LLM_VIA=fiber`: measured Soft in-fiber `http-post` (std/llm) → `llm_via=fiber`; denseness `fiber_graph` ≠ in-fiber LLM. Stamp `llm_parallel=fiber` only when a concurrent Soft-fiber batch (≥2) measured ok this round; else `fiber_serial` / host fallback. Soft Ready `std::println` status hangs on raw `{` in `value` (aura-build #1 fixed client parse only). Default fiber LLM is **in-memory Soft join** of `(base64-encode (http-post …))` (request body embedded when small); `write-file` is opt-in only (`AURA_BUILD_FIBER_LLM_MODE=write_file`) / inefficient
- `concurrent_llm=true` + `llm_parallel_ok` when ≥2 worldlines have `tools_used` containing `llm` in the same round
- `orch_observation.ok` only when Soft `(engine:metrics "query:orch-module-stats")` returns a live hash (sentinel via Soft hash-values `2589` hits; Soft string `hash-ref` is opaque)
- `repair_path=soft_session_worldline` when prefer-session verify is on the live Soft holder

## See also

- [architecture.md](architecture.md) — layers
- [storm-still-incr.md](storm-still-incr.md) — prove-or-refuse
- [trajectory-protocol-v0.md](trajectory-protocol-v0.md) — `runtime.session_model`
- [iteration-plan.md](iteration-plan.md) — deferred checklist
