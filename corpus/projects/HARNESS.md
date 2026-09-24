# Projects Aura corpus harness

Combat/dogfood-aligned multi-file systems (8–20 `.aura` files).

## Layout per `corpus/projects/<slug>/`

| Path | Role |
|------|------|
| `GOAL.md` | Requirements + module APIs + scenario (same as dogfood projects) |
| `spec.md` | Copy of GOAL.md |
| `dogfood.json` | `files`, `entry`, `run_mode=cli_multi`, `expect` / `expect_res` from tests |
| `ref/` | Python reference + `run_scenarios.py` |
| `tests.json` | Measured KEY=value expect lines (only place for expected outputs) |
| `src/` / `src_2/` | MiniMax Aura candidates (variants) |
| `stub/` | Copy of primary `src/` for `aura-build llm-dogfood --project` / combat |
| `meta.json` | Measured parse/run/pass + tokens |

## Run convention

```bash
$AURA_BIN $(jq -r '.files[]' dogfood.json | sed 's|^|src/|')
# or from stub/:
$AURA_BIN file1.aura … main.aura
```

## Expect

Stdout KEY=value lines; expected values ONLY in `tests.json` / dogfood `expect`
(measured by running `ref/run_scenarios.py`). Anti-hardcode applies to Aura sources.
