# Trajectory protocol v0

Every `aura-build run` appends one **episode** (JSON object) per line to a JSONL file.

## Episode schema

```json
{
  "schema_version": "trajectory.v0",
  "episode_id": "uuid",
  "ts_start": "ISO-8601",
  "ts_end": "ISO-8601",
  "prompt": "string",
  "runtime": {
    "mode": "simulated | aura",
    "requested_mode": "simulated | aura | auto",
    "aura_ref": "optional string/path",
    "seed": 0
  },
  "harness": {
    "l1_strategy_id": "string",
    "l2_weights_id": null,
    "l3_online": false
  },
  "worldlines": [
    {
      "id": "wl-0",
      "parent_id": null,
      "mutations": [
        {
          "op": "simulated_edit",
          "target_id": "node:demo",
          "summary": "string"
        }
      ],
      "eval": {
        "fitness": 0.0,
        "passed": true,
        "metrics": {
          "tests_passed": 1,
          "tests_total": 1,
          "incr_compile_ms": 0,
          "audit_ok": true
        },
        "notes": "string"
      }
    }
  ],
  "selected_id": "wl-0",
  "selection_reason": "max_fitness",
  "privacy": {
    "redacted": false,
    "retention_class": "dogfood"
  }
}
```

### Required fields

`schema_version`, `episode_id`, `ts_start`, `ts_end`, `prompt`, `runtime.mode`, `worldlines` (≥1), `selected_id`, `harness.l3_online`.

`selected_id` must match one `worldlines[].id`. Fitness is comparable within an episode only.

**Honesty:** `runtime.mode` is the backend that actually ran. `requested_mode` may be `auto`; never claim `aura` when the episode used `SimulatedBackend`. M1 `AuraBackend` is a subprocess bridge (mutate:rebind + eval-current), not fiber-live multi-worldline.

### M2 extensions (optional keys)

| Field | Meaning |
|-------|---------|
| `runtime.profile` | e.g. `{id: aura-repo, root, fitness_source, incr_claimed, incr_proven}` |
| `runtime.workspace` | Shared worldline workspace path |
| `runtime.session_model` | `shared_workspace_subprocess` (M2 default) or future `long_lived_aura` |
| `runtime.parent_ref` / `stable_refs` | Parent snapshot + candidate stable refs |
| `runtime.incr_proven` | **Must be false** until storm-still-incr is measured |
| `worldlines[].stable_ref` / `parent_id` | Continuity across candidates |
| `worldlines[].eval.metrics.compile_ms` | Wall-clock compile/check ms |
| `worldlines[].eval.metrics.incr_claimed` | Profile claims incremental path |
| `worldlines[].eval.metrics.incr_proven` | Proven incr; false in M2 |
| `discarded[]` | Losers after select-best (`id`, `reason`, `fitness`, `stable_ref`) |

Do not treat `stable_ref` or `session_model=shared_workspace_subprocess` as fiber-live FlatAST.

### M3 extensions (optional keys)

| Field | Meaning |
|-------|---------|
| `harness.mid` | Mutation id for a harness change |
| `harness.actions[]` | Ordered `propose` / `canary` / `commit` / `heal` / `discard` |
| `harness.outcome` | Final decision for a canary episode |
| `harness.autopropote` / `harness.committed` | Promote gate (default off) |
| `harness.config` / `config_base` / `config_proposed` | Harness snapshots |
| `harness.l2_ref` | Stub `{weights_id, loaded, stub:true}` — no training |
| `runtime.shadow` / `runtime.harness_canary` | Canary ran on shadow profile |
| `memory.profile_id` | Optional memory profile touched by orch |

AUTOPROMOTE default is **OFF**. Canary reject → `heal` (live harness unchanged). Pass + autopropote off → `discard`. Pass + autopropote on → `commit` to `.aura-build/harness.json`.

`incr_proven` remains **false**. Do not treat harness commit as fiber-live FlatAST.

## Export formats

| Format | Use |
|--------|-----|
| **JSONL** (default) | Append-only local / CI artifact |
| **JSON array** | Batch export for training jobs |
| **Parquet** (M4+) | Columnar RL pipelines |

M0 writes JSONL only. Schema validation rejects unknown `schema_version` and missing required keys.

## Privacy

- Default `retention_class`: `dogfood` | `ci` | `customer` | `ephemeral`.
- Prompts and mutation summaries may contain secrets — callers must set `privacy.redacted=true` when scrubbing.
- Customer trajectories never train shared L2/L3 without explicit contract.
- Prefer stable node IDs over file path dumps when exporting.

## Devaluation of off-runtime data

Chat transcripts, raw git diffs without eval metrics, and Postman-style request logs are **devalued** for training and moat claims. Preference order:

1. On-runtime mutate → eval → select episodes (this protocol)
2. Reproducible replay under pinned Aura + seed
3. Everything else (auxiliary only)

## L1 / L2 / L3 linkage

| Field | Meaning |
|-------|---------|
| `harness.l1_strategy_id` | Which strategy code produced the scout/mutate policy |
| `harness.l2_weights_id` | Offline weights id, or null |
| `harness.l3_online` | Must be `false` unless experimental online path is explicitly enabled |

Episodes produced under `l3_online=true` are tagged and quarantined from default L2 promotion sets.
