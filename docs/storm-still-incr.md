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

1. Optional **fiber session probe** — looks for an explicit
   `AURA_BUILD_FIBER_SESSION_OK` marker. Absent that, session stays
   `shared_workspace_subprocess` (one-shot subprocess multi-eval ≠ fiber).
2. Run **N cycles × W concurrent worldlines** of mutate+eval via `AuraBackend`.
3. Set `incr_proven=true` **only if** every cycle is `ok` **and** carries an
   **explicit incr-valid signal** (`metrics.incr_valid`, `metrics.incr_proven`,
   or notes containing `AURA_BUILD_INCR_VALID`).
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
| `session_model` | `shared_workspace_subprocess` unless fiber probe proves otherwise |
| `fiber_live` | True only with explicit fiber session OK |
| `cycles_*` | Requested / completed / ok / incr_valid counts |
| `storm[]` | Per-cycle results |

## Trajectory / doctor wiring

- Latest report: `.aura-build/prove-incr-latest.json`
- `aura-build doctor` surfaces probe + last report + honesty flags
- `aura-build tui` / `acp status` overlay `honesty.incr_proven` /
  `fiber_live` from that report when present (still default **false**)
- Orch episodes still default `runtime.incr_proven=false`; they do **not**
  silently flip because a report exists — attach explicitly if needed

## Deferred

- Real FlatAST incr-compile telemetry from Aura (marker / metric)
- Long-lived fiber-hosted multi-worldline session API
- Auto-promoting orch `runtime.incr_proven` from prove-incr (opt-in later)
