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
| `runtime.session_model` | `shared_workspace_subprocess` (file) or `fiber_denseness_in_process` when denseness live |
| `runtime.worldline_backend` | `fiber_graph` (fiber:spawn fan-out) or `file` (parent/candidates/) — never faked |
| `runtime.fiber_live` | Denseness probe result; env alone cannot elevate |
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
| `harness.l2_ref` | `{weights_id, loaded, stub:true, artifact_present}` — metadata JSON only; no tensors |
| `runtime.shadow` / `runtime.harness_canary` | Canary ran on shadow profile |
| `memory.profile_id` | Optional memory profile touched by orch |

AUTOPROMOTE default is **OFF**. Canary reject → `heal` (live harness unchanged). Pass + autopropote off → `discard`. Pass + autopropote on → `commit` to `.aura-build/harness.json`.

`incr_proven` remains **false**. Do not treat harness commit as fiber-live FlatAST.

### M4 export metadata (optional keys on exported episodes)

| Field | Meaning |
|-------|---------|
| `privacy.export_filter` | e.g. `m4.default` when redaction ran |
| `privacy.redacted` | `true` after default export filter |

Batch export does not add training labels; distillers read actions / fitness / `harness.mid` as documented in [specialist-training-notes.md](specialist-training-notes.md).

## Export formats

| Format | Use |
|--------|-----|
| **JSONL** (default) | Append-only local / CI artifact |
| **JSON array** | Batch export for training jobs (`aura-build export`) |
| **Parquet** (optional) | Columnar RL pipelines when pandas+pyarrow installed |

M0–M3 write JSONL. **M4** `aura-build export` always writes a JSON array of validated episodes; Parquet is best-effort (optional dep). Schema validation rejects unknown `schema_version` and missing required keys.

### M4 privacy filters (default ON)

- Absolute local paths → `<redacted:path:basename>` placeholders
- Secret / token patterns (`api_key=…`, `sk-…`, `ghp_…`, `Bearer …`, etc.) → `<redacted:secret>`
- Sets `privacy.redacted=true` and `privacy.export_filter=m4.default`
- `--include-raw` / `--no-redact` skips filters (local dogfood only)
- Does **not** flip `incr_proven` or enable `l3_online`

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

### Post-M5 prove-incr metadata (auto-attach on `run`)

| Field / artifact | Meaning |
|------------------|---------|
| `.aura-build/prove-incr-latest.json` | Latest prove-or-refuse report (`prove_incr.v0`) |
| `runtime.incr_proven` | Mirrored from attach; **false** unless report measured + proven |
| `runtime.measured` / `fiber_live` / `session_model` | Mirrored honesty fields (never invented true) |
| `runtime.prove_incr` | Attach block: `reason`, `source`, `env_notes`, `attached`, gates |
| ACP/TUI `honesty.*` | May overlay last prove report when present |

`aura-build run` defaults `--attach-prove` (cheap). Env
`AURA_BUILD_INCR_VALID` / `AURA_BUILD_FIBER_SESSION_OK` alone cannot force
true — see [storm-still-incr.md](storm-still-incr.md). Wall-clock alone
never proves incr.

