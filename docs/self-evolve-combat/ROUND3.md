# ROUND3 — Soft #4055 live denseness + mini-exchange without gold/intent

**When:** 2026-09-24 Asia/Shanghai (CST, UTC+8)  
**Aura tip:** `bd1c610` — `fix(stdlib): native encoding prims — base64/hex O(n²) EDSL folds OOM'd Soft denseness (#4055)`  
**Soft Ready binary:** `/workspace/aura-grok/build_soft4055/aura` (RelWithDebInfo ≡ `build_soft4048` profile, workers=1)  
**aura-build tips:** `a518797` → `760a9ee` (repair-context iteration)  
**MiniMax:** propose-only (`MiniMax-M3`). No gold/intent (`--explore-tools llm`).

## Soft #4055 — local stubs

| Check | Result |
|-------|--------|
| `check_soft_ready_http_post_two_batch_4054.py` | **PASS** N=2 batches=2 |
| `check_soft_ready_http_post_three_batch_4055.py` pad=8192 | **PASS** N=3×3 RSS peak ~78 MB |
| same, `AURA_4055_BODY_PAD=65536` | **PASS** N=3×3 RSS peak ~80 MB |

## Soft #4055 — live MiniMax denseness (≥5 × N=3, one Soft `--serve-async`)

| batch | N | wall_ms | ok | llm_via | llm_parallel | ping |
|------:|--:|--------:|:--:|---------|--------------|:----:|
| probe | 1 | 6813 | ✓ | fiber | — | — |
| 1 | 3 | 5592 | ✓ | fiber | fiber | ✓ |
| 2 | 3 | 3971 | ✓ | fiber | fiber | ✓ |
| 3 | 3 | 5972 | ✓ | fiber | fiber | ✓ |
| 4 | 3 | 5836 | ✓ | fiber | fiber | ✓ |
| 5 | 3 | 3316 | ✓ | fiber | fiber | ✓ |

**Verdict:** #4055 **holds** well past the old 3rd-batch live MiniMax wedge. No Soft reopen.

## Combat — mini-exchange pure MiniMax

```bash
export AURA_BIN=/workspace/aura-grok/build_soft4055/aura
aura-build self-evolve combat \
  --project examples/projects/mini-exchange \
  --start-session --fiber-explore 3 --concurrent-llm --fiber-llm \
  --explore-tools llm --max-rounds 8 --no-push --json \
  --env-file ~/.config/aura-build/minimax.env
```

### Run A — pre-prompt-fix — `combat_20260924-172306` (~17:23–17:31 CST)

8 rounds, ok=False `max_rounds_8`. Soft denseness fiber through r0–r6; r7 `llm_parallel=fiber_serial` (`partial_ok:2/3`). No session loss.

### Run B — after `a518797` — `combat_20260924-173546` (~17:35–17:46 CST)

Still max_rounds. Dominant: `FILL1=filled`, unbalanced parens. Soft fiber stable; r3/r7 honest `fiber_serial` / `http_post_or_b64_missing` without detach.

### Run C — after `760a9ee` FILL1/parens scaffolding — `combat_20260924-174643` (~17:46–17:53 CST)

| round | llm_via | llm_parallel | explore_parallel | explore_wall_ms | passed | fail sketch |
|------:|---------|--------------|------------------|----------------:|:------:|-------------|
| 0 | fiber | fiber | fiber_graph | 11447 | ✗ | parse `)` |
| 1 | fiber | fiber | fiber_graph | 12868 | ✗ | FILL1=filled |
| 2 | fiber | fiber | fiber_graph | 13931 | ✗ | FILL1=filled |
| 3 | fiber | fiber | fiber_graph | 12892 | ✗ | parse `)` |
| 4 | fiber | fiber | fiber_graph | 10463 | ✗ | FILL1=filled |
| 5 | fiber | fiber | fiber_graph | 11817 | ✗ | FILL1=filled |
| 6 | fiber | fiber | fiber_graph | 13079 | ✗ | unbalanced paren warn |
| 7 | fiber | fiber | fiber_graph | 13094 | ✗ | unbalanced paren warn |

**All 8 rounds** stayed `llm_via=fiber` / `llm_parallel=fiber` / `explore_parallel=fiber_graph`. Soft path fully green for denseness; MiniMax did not converge.

## aura-build product changes

| SHA | Change |
|-----|--------|
| `a518797` | Multi-file repair: verify stderr↑, interface/scenario contracts, implicated full bodies + peer signatures; richer exchange `user_extra` |
| `760a9ee` | Force order/match/query/main when FILL1≠partial; stub-hardcode + paren-only-turn scaffolding |

## Dual sink

| Class | Action |
|-------|--------|
| Soft live MiniMax denseness ≥5×N=3 | **Done** — Aura #4055 `bd1c610` verified; comment on issue |
| mini-exchange concurrent-llm w/o gold | **aura-build residual** — still max_rounds on FILL1/parens after prompt iteration |
| Occasional `fiber_serial` / `partial_ok` | Honest measurement; not a Soft wedge |

## Honesty

Never env-elevated `fiber_live` / `fiber_graph` / `llm_parallel=fiber` / `incr_proven`. Soft Ready workers=1; Soft denseness banner only. MiniMax propose-only; gold/intent not selected.

## Recommended next tier

1. aura-build: per-file Aura parse gate before accepting a worldline rewrite; structured single-file patch format; optional longer max-rounds once syntax gate lands.
2. Or dogfood **mini-clearing** / **mini-oms** after exchange concurrent-llm greens.
3. Soft: optional dig on rare `http_post_or_b64_missing` under long sessions — **not** a #4055 reopen.

## Course correction — contract_heal reverted (2026-09-24 ~18:20 CST)

Parent steering: `487bcf3` / `319e4a7` GOAL-contract heal = gold under another name. **Reverted** (`06e27fb`, `dde6bd2`). Offline "green" via heal is **not** reportable as pure-MiniMax.

**Still valid product levers:** elitist carry, per-file Aura parse gate, finer expect-line fitness, honest llm_parallel aggregate (`12eaaba`); GOAL.md + failing verify lines + implicated files; staged few-file repair; more candidates/rounds. Fixture-specific FEES=14/EQ=1/FILL1 literals removed from product repair helpers (derive from verify diffs + GOAL text).

**Honest best pure MiniMax so far:** fitness **0.7385** @ `combat_20260924-175921` (not green). Next: ≤3 generic-only combat attempts.


### Run 3h — generic-only after heal revert — `combat_20260924-182234` (18:22–18:33 CST)

Trajectory fitness climbed 0.31→0.52→0.63→0.85→**1.0** (round 8) with Soft `llm_parallel=fiber` (8/9; 1×fiber_serial). **Not claimed green:** main hardcodes STP=0 and COUNT=10. Anti-hardcode product gate added; continuing ≤2 more attempts.

