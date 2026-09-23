# Storm-still-incr — prove-or-refuse (Post-M5)

## Goal

Measure whether multi-candidate mutate→eval under concurrent worldline
pressure **stayed incremental**. If we cannot measure it honestly on this
runtime, **refuse**: write `incr_proven=false` with a reason. Never set
`incr_proven=true` from vibes, wall-clock alone, or a simulated backend.

## How to run

```bash
# Prove-or-refuse (writes .aura-build/prove-incr-latest.json)
aura-build prove-incr
aura-build prove-incr --cycles 8 --worldlines 3 --json

# Aggregate health + last report
aura-build doctor
aura-build doctor --json
```

Optional: `AURA_BIN` / `--aura-bin`, `AURA_REF` / `--aura-ref`.

Script wrapper (same logic):

```bash
./scripts/prove_incr.sh
```

## Fail-closed (expected on many boxes)

If the Aura binary is **missing** or **unhealthy** (classic:
`GLIBCXX_… not found`), the harness:

1. Does **not** invent a successful storm
2. Writes a report with `incr_proven=false`
3. Sets `reason` to a stable token (`aura_glibcxx_mismatch`,
   `aura_binary_missing`, …)
4. Keeps `session_model=shared_workspace_subprocess`, `fiber_live=false`
5. Exits **0** — refuse is a successful honesty outcome (CI-green)

## Healthy path

When `probe_aura` succeeds:

1. **Fiber session probe** (honest denseness) — under `AURA_BIN`, attempt
   `fiber:spawn`+`fiber:join` oneshot and same-FlatAST dual-candidate
   `mutate:rebind` denseness (see aura-grok `docs/stdlib/fiber-spawn.md`).
   Optional child `--serve-async-bench` probe records `serve_session_ok`
   (often false on Soft/Ready boxes). Set `fiber_live=true` and
   `session_model=fiber_denseness_in_process` **only** if denseness
   succeeds. `AURA_BUILD_FIBER_SESSION_OK` alone never elevates
   (`env_fiber_ignored_unproven` when set while still false).
   `--no-fiber-probe` / `AURA_BUILD_NO_FIBER_PROBE=1` skips and keeps false.
2. Run **N cycles × W concurrent worldlines** of mutate+eval via `AuraBackend`.
3. Set `incr_proven=true` **only if** every cycle is `ok` **and** carries an
   **explicit incr-valid signal** (`metrics.incr_valid`, `metrics.incr_proven`,
   notes containing `AURA_BUILD_INCR_VALID`, or parsed `AURA_INCR_VALID=1`).
   The Aura bridge derives that signal from real `compile:epoch` /
   `hotswap-invalidate-total` / `mutation-epoch` deltas (never wall-clock).
4. Otherwise refuse with
   `storm_cycles_ok_but_no_incr_valid_signal:…` or `storm_cycles_failed:…`.

Wall-clock `incr_compile_ms` alone is **not** proof.

## Report shape (`prove_incr.v0`)

| Field | Meaning |
|-------|---------|
| `incr_proven` | True only after measured incr-valid signal on all cycles |
| `reason` | Stable refuse / prove token |
| `measured` | True iff a storm actually ran |
| `aura_healthy` | Probe result |
| `session_model` | `shared_workspace_subprocess` or `fiber_denseness_in_process` when denseness probe passes |
| `fiber_live` | True only after successful spawn+join denseness probe (never from env alone) |
| `cycles_*` | Requested / completed / ok / incr_valid counts |
| `storm[]` | Per-cycle results |

## Trajectory / doctor wiring

- Latest report: `.aura-build/prove-incr-latest.json`
- `aura-build doctor` surfaces probe + last report + honesty flags
- `aura-build tui` / `acp status` overlay `honesty.incr_proven` /
  `fiber_live` from that report when present (still default **false**)
- **`aura-build run` auto-attaches** prove honesty into every episode
  (`--attach-prove`, default **ON**; `--no-attach-prove` to skip):
  - `runtime.incr_proven` / `measured` / `fiber_live` / `session_model`
  - `runtime.prove_incr.{reason,source,env_notes,attached,…}`
  - Source: latest report, else lightweight doctor snapshot defaults
  - **Never invents true** — missing/unhealthy report ⇒ false

### Env gates (read-only honor)

| Env | Effect on attach |
|-----|------------------|
| `AURA_BUILD_INCR_VALID=1` | Documents future/external telemetry intent. If set while prove says false → keep `incr_proven=false` + `env_notes: env_ignored_unproven`. Cannot alone elevate. |
| `AURA_BUILD_FIBER_SESSION_OK=1` | Read-only intent marker. Without successful denseness probe, keep `fiber_live=false` + `env_fiber_ignored_unproven`. Cannot alone elevate. |

These gates exist so healthy boxes can advertise readiness; attach still
requires the prove harness (or an explicit measured report) to agree.


## Toolchain: GLIBCXX_3.4.35 (host vs Aura)

**Measured on this dogfood box (2026-09-23 CST):**

| Item | Value |
|------|-------|
| Aura binary | `/workspace/aura-redis/.deps/aura/build/aura` (also check `/workspace/aura-grok`) |
| Built with | GCC 16.1.0 (`GCC: (Ubuntu 16.1.0-2ubuntu1) 16.1.0` in `.comment`) |
| Binary needs | **GLIBCXX_3.4.35** (and down to 3.4) |
| Host `libstdc++` | `/lib/x86_64-linux-gnu/libstdc++.so.6` → `libstdc++.so.6.0.33` |
| Host max symbol | **GLIBCXX_3.4.33** (Debian 13 / g++ 14.2.0) |
| Host `g++` | 14.2.0 — **cannot** rebuild Aura (tree is **C++26 / GCC 16** modules) |

Mismatch ⇒ probe fails ⇒ `reason=aura_glibcxx_mismatch`, `incr_proven=false`,
`measured=false`. That is correct honesty, not a green to invent.

### Why not “just rebuild on the box”?

`aura-grok` / pinned Aura set `CMAKE_CXX_STANDARD 26` and target GCC 16
(presets literally say “GCC 16”). Host g++-14 cannot compile that tree.
Official Aura toolchain image: `ghcr.io/cybrid-systems/dev:v1.0.7`.

### Minimal host workaround (dogfood without fake green)

1. Extract a matching `libstdc++.so.6.0.35` (+ `libgcc_s.so.1`) from the
   toolchain image into a **sidecar** dir (gitignored under redis `.deps/`):

   ```bash
   ./scripts/fetch-gcc16-libstdcxx.sh
   # default dest: /workspace/aura-redis/.deps/gcc16-libstdcxx
   ```

2. `aura-build` auto-prepends that dir to `LD_LIBRARY_PATH` when probing /
   running Aura (`AURA_LIBSTDCXX_DIR` overrides). No need to commit the `.so`.

3. Re-run:

   ```bash
   aura-build doctor --json
   aura-build prove-incr --json
   ```

Expect: `aura_healthy=true` / probe ok once the sidecar is present.
With a healthy Aura that exposes `compile:epoch` /
`query:jit-stats-hash`, storm cycles should carry `AURA_BUILD_INCR_VALID 1`
and `incr_proven` can become **true**. If the marker is absent, refuse stays
correct — do **not** flip it by hand.

### Alternatives (same honesty)

- Run prove-incr **inside** `ghcr.io/cybrid-systems/dev:v1.0.7` (full GCC16).
- Install/use a host GCC ≥15 libstdc++ (conda / newer distro) and point
  `AURA_LIBSTDCXX_DIR` at it.
- Static-link `libstdc++` when building Aura in-container (heavier; not done here).

## Incr-valid probe contract (Aura ↔ aura-build)

Prefer **existing Aura stats** over inventing a counter. The mutate+eval bridge
(`AuraBackend` / `scripts/aura_m1_mutate_eval.aura`) measures language-wide
surfaces documented in Aura `docs/stdlib/hot-strategy.md` (Issue #2684):

| Surface | Role |
|---------|------|
| `(stats:get "compile:epoch")` | Mutation / compile epoch; bumps on `mutate:rebind` |
| `query:jit-stats-hash` → `hotswap-invalidate-total` | Lifetime invalidate count; stays elevated after eval |
| `query:jit-stats-hash` → `mutation-epoch` | Same clock family; delta after rebind |

**Aura program emits (stdout):**

```text
AURA_BUILD_OK <int>
AURA_INCR_META epoch=<pre>-><post> inv=<pre>-><post> mut=<pre>-><post>
AURA_BUILD_INCR_VALID 1
AURA_INCR_VALID=1
```

only when `(or (> epoch1 epoch0) (> inv1 inv0) (> mut1 mut0))`. Otherwise
`AURA_BUILD_INCR_VALID 0` (no env line).

**aura-build parser** (`runtime.parse_incr_valid_signal`):

- Accepts `AURA_BUILD_INCR_VALID 1` **or** `AURA_INCR_VALID=1` on stdout/stderr
- Rejects `… 0`, missing marker, or failed eval (`incr_valid=false`)
- Sets `eval.metrics.incr_valid` + includes `AURA_BUILD_INCR_VALID` in notes
- `prove-incr` sets `incr_proven=true` **only** when every storm cycle has that signal

Demo (healthy Aura + GCC16 sidecar on this box):

```bash
./scripts/demo_incr_valid_probe.sh
# or:
aura-build prove-incr --cycles 2 --worldlines 1 --json
```

If Aura cannot emit the marker (old binary / missing stats primitives), keep
refuse with `storm_cycles_ok_but_no_incr_valid_signal` — do **not** invent true.

No Aura C++ change was required for this contract; Redis-specific hooks stay out.

## Deferred

- Lift worldlines onto fiber graph / long-lived serve-async session (slice 3; needs fiber denseness probe OK)
- `serve_session_ok` / scheduler backend on Soft boxes (production Ready self-check)
- Richer FlatAST metrics JSON file path (optional alternate to stdout markers)
