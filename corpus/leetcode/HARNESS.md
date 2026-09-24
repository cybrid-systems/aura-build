# LeetCode Aura corpus harness

## Layout

- `catalog.jsonl` — problem index (`slug`, `title`, `category`, `statement`)
- `<slug>/problem.md` — statement adapted to this harness
- `<slug>/ref.py` — Python reference; run → stdout JSON → `tests.json`
- `<slug>/tests.json` — `[{id, input, expected}, ...]` measured from ref.py
- `<slug>/solution.aura` / `solution_N.aura` — MiniMax Aura candidates
- `<slug>/meta.json` — measured parse/run/pass + token usage (facts only)

## Stdin-less Aura convention

1. Define `(solve ...)` for the problem.
2. Embed test inputs as literals; for each case `i` print one line:
   `CASEi=<value>` via `(display "CASEi=")(display ...)(newline)`.
3. Expected values live **only** in `tests.json` — do not treat hardcoded
   `display` of expected answers as a correct solution (anti-hardcode).

## Comparison

Host parses `CASEi=` lines from Aura stdout and compares string equality to
`tests.json[].expected` (canonical JSON literals from ref.py).
