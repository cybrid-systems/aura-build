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
