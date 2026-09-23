# Soft Ready gate (`--serve-async` / #3098 → Aura #4047)

> **Status (Aura tip with #4047):** Soft boxes (`AURA_SANDBOX=off`) can enter
> `--serve-async` under an honest **Soft Ready** profile. Probe expects
> `ok=true` / `serve_mode_preferred=async` and stderr Soft Ready banner —
> **not** production multi-worker Ready. Never env-fake.

> Historical Soft refuse (pre-#4047) is documented below for tip decoding.


> Measured on Soft boxes (`AURA_SANDBOX=off`). SSOT companion to
> [optimal-dev-loop.md](optimal-dev-loop.md). Never env-fake Soft Ready /
> `serve_mode=async` / `serve_cross_session_shared_ast`.

## What we measure on this box (post Aura #4047)

```text
aura: Soft Ready profile (#4047): multi-worker serve under Soft contracts —
NOT production multi-worker Ready. Do not stamp production Ready /
production_defaults from this path.
```

Standalone probe (aura-build):

```bash
export AURA_BIN=/workspace/aura-redis/.deps/aura/build/aura   # or tip build/aura
python -c 'from aura_build.serve_session import probe_serve_async_soft_ready
import json,os; r=probe_serve_async_soft_ready(os.environ["AURA_BIN"]); print(json.dumps(r,indent=2))'
# → ok=true serve_mode_preferred=async reason=soft_ready_profile_4047
```

Holder starts `aura --serve-async` and stamps `serve_mode=async` when probe ok.
`serve_cross_session_shared_ast` still requires measured orch→project binding
proof (binding-level share deferred; Soft --serve sessions remain separate
CompilerServices).

### Historical Soft refuse (pre-#4047 tips)

```text
FATAL: production multi-worker Ready self-check failed (#3098 + #2955 + #3195)
fail_bits=0x10 — … Soft … under multi-worker is refused.
```

## `fail_bits` map (Aura `runtime_production_abi.h`)

| Bit | Mask | Name | Meaning |
|-----|------|------|---------|
| 0 | `0x01` | `abi_steal_complete` | strong steal-complete marker missing (#2955) |
| 1 | `0x02` | `abi_eval_id` | strong eval-id marker missing |
| 2 | `0x04` | `abi_mutation_held` | strong mutation-held marker missing |
| 3 | `0x08` | `abi_depth_from_ptr` | strong depth-from-ptr marker missing |
| **4** | **`0x10`** | **`defaults_missing_soft`** | **Soft / `AURA_SANDBOX=off` / `!production_defaults_active` (#3098)** |
| 5 | `0x20` | `residual_sticky` | residual-zero sticky wiring (#3195) |
| 6 | `0x40` | `tenant_scope` | tenant-scope resume ABI (#3275) |
| 7 | `0x80` | `probe_linear` | steal linear-probe ABI (#3343) |
| 8 | `0x100` | `typed_entry` | JIT typed-entry ABI (#3419) |
| 9 | `0x200` | `hot_contracts` | hot contracts not fail-closed (#3866) |

**This Soft box:** `fail_bits=0x10` → **only** bit 4 (`defaults_missing_soft`).
No ABI-marker bits are set; the refuse is the Soft defaults gate itself.

Decode helper: `aura_build.serve_session.decode_soft_ready_fail_bits("0x10")`.

## Why aura-build cannot clear it in this slice

`aura_runtime_require_production_multi_worker()` (#3098) **never** returns
true without abort when Soft (`sandbox=off`) or `!production_defaults_active`.
Wired from `main.cpp` for `--serve-async` / multi-worker entry.

Clearing Soft Ready here would require one of:

1. **Aura runtime change** — allow Soft ergonomics for `--serve-async` (or a
   Soft-only shared_workspace path) — out of aura-build scope.
2. **Env flip to production sandbox** — would claim production Ready while
   the box remains Soft ergonomics; **forbidden** (honesty: never env-fake
   Soft Ready / async / shared_ast).

So: **blocker = Aura Soft Ready gate**, not a missing aura-build config flag.

## What still works (same-session optimal loop)

| Flag | Soft `--serve` today |
|------|----------------------|
| `serve_mode` | `sync` (honest) |
| `serve_async_soft_ready.ok` | `false` (`fail_bits=0x10`) |
| `serve_cross_session_shared_ast` | `false` (separate CompilerServices) |
| `serve_same_session_mutate_ok` | **`true`** (measured mutate:rebind + eval) |
| `session dogfood` / `pursue --prefer-session` | **`path_kind=mutate_rebind`**, `cold_spawns=0` |

## Next Soft gate (precise)

1. Aura allows Soft `--serve-async` **or** Soft shared_workspace_tree across
   named sessions without production multi-worker Ready.
2. Re-run Soft Ready probe → `ok=true`, holder starts async.
3. Re-measure cross-session binding (`orch` define visible in `project`) →
   stamp `serve_cross_session_shared_ast=true` **only if proven**.
4. Then orch/project dual-session fiber worldlines on one shared FlatAST.

Until then: deepen same-session `mutate:rebind` (session dogfood + pursue).

## How to run (box)

```bash
export AURA_BIN=/workspace/aura-redis/.deps/aura/build/aura
aura-build session start
aura-build session status --json   # serve_mode=sync; soft_ready.ok=false; same_session_mutate=true
aura-build session dogfood --rounds 3 --json
aura-build pursue --goal "emit GREET=aura" --min-fitness 0.8 --max-rounds 2 --worldlines 3 --json
# → worldline_backend=serve_mutate_rebind path_kind=mutate_rebind cold_spawns=0
aura-build session stop
```

Force cold Aura kernel pursue (skip session): `pursue --force-kernel …`.
