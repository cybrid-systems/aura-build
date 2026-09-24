# DAG-Scheduled Volcano Engine — GOAL.md

## 1. Overview

A miniature **DAG-scheduled Volcano-style executor** built in Aura. A logical query plan is represented as a graph of **operators** (`scan`, `filter`, `project`, `join`, `aggregate`, `sink`). The executor:

1. Computes operator dependencies (edges: child → parent for data flow).
2. Performs a **topological ordering** with **cycle detection**.
3. Identifies **pipeline breakers** (e.g. `aggregate`, `join`'s build side).
4. Schedules operators into **pipeline fragments** (chains of non-breaking operators).
5. Within each fragment, uses **morsel-driven parallel execution**: operators pull a morsel (a small chunk of rows) from their child, process it, and push to parent.
6. Tracks per-operator row counts, elapsed "ticks", and parallelism decisions.
7. Drives everything off an explicit **DAG tick loop** that fires all ready fragments concurrently (simulated via a step counter, not OS threads — Aura has no threading).

The output is a deterministic snapshot of the executed plan suitable for verifying the executor's scheduling behavior.

---

## 2. Exact stdout contract

After loading all modules and running `main.aura`, the program MUST print exactly these `KEY=value` lines **in this order**, one per line, terminated by a single trailing newline:



That is **15 keys** (within the 8–16 target band). All values are deterministic given the canned plan encoded in `main.aura`.

---

## 3. Module table

Each `.aura` file is loaded in the order shown. Only `main.aura` performs `display`. All other files only `define` (and may `define` small private helpers).

| # | File | Required exported `define` forms |
|---|------|-----------------------------------|
| 1 | `op.aura` | `(op-make name kind inputs)`, `(op-name op)`, `(op-kind op)`, `(op-inputs op)`, `(op-rows op)`, `(op-add-rows! op n)` |
| 2 | `plan.aura` | `(plan-build ops edges)` → plan alist, `(plan-nodes p)`, `(plan-edges p)`, `(plan-valid? p)` (cycle check via topo) |
| 3 | `toposort.aura` | `(toposort nodes edges)` → ordered list, `(toposort-detect-cycle nodes edges)` → `#t`/`#f` |
| 4 | `breaker.aura` | `(breaker? op-kind)` → `#t`/`#f`, `(breaker-kinds)` → list of breaker kinds |
| 5 | `fragment.aura` | `(fragment-build topo breakers)` → list of fragments (each a list of op-names), `(fragment-count frags)` |
| 6 | `morsel.aura` | `(morsel-size)`, `(morsel-slice rows size)` → list of morsels (sublists of ≤ size) |
| 7 | `rowbuf.aura` | `(rowbuf-new)`, `(rowbuf-push! buf rows)`, `(rowbuf-drain! buf)` → list, `(rowbuf-count buf)` |
| 8 | `exec.aura` | `(exec-run plan morsel-size)` → result alist with `:ticks`, `:fragments`, per-op `:rows`, `:sunk-rows` |
| 9 | `sched.aura` | `(sched-step frags state)` → next state (mutates via `set!` on state list), `(sched-ready? frag state)` |
| 10 | `metrics.aura` | `(metrics-init)`, `(metrics-tick! m)`, `(metrics-record! m op rows)`, `(metrics-snapshot m)` |
| 11 | `report.aura` | `(report-format metrics plan frags)` → alist of `KEY . value` pairs ready for `display` |
| 12 | `scan_op.aura` | `(scan-emit op n)` → row list of length n (synthesized ints) |
| 13 | `filter_op.aura` | `(filter-emit rows)` → even-only rows (modulo-2 filter) |
| 14 | `join_op.aura` | `(join-emit left-rows right-rows)` → paired/cartesian-reduced rows |
| 15 | `main.aura` | loads plan → calls `exec-run` → calls `report-format` → prints lines |

> Note: the file count is **15**, satisfying the 8–20 target. The "executor" sits in `exec.aura`/`sched.aura`; operator logic in `scan_op.aura`/`filter_op.aura`/`join_op.aura`; per-op `project`/`aggregate`/`sink` behavior is folded into `exec.aura` (the API surface stays small — see anti-hardcode rule §5).

---

## 4. Scenario steps (executed by `main.aura`)

1. **Build the canned logical plan** with 6 operators and 7 dependency edges:
   - `scan → filter → project → join → aggregate → sink`
   - plus a second `scan` feeding `join` (so `join` has 2 inputs).
2. Call `plan-build` → `(plan-valid? p)` must be `#t`.
3. Call `toposort` → verify the returned ordering matches the canonical 6-name sequence above.
4. Call `breaker?` for each op kind → assemble `DAG_BREAKERS` list.
5. Call `fragment-build` → must yield exactly 2 fragments (`[scan,filter,project]` and `[join,aggregate,sink]`).
6. Set morsel size = 64 (constant in `main.aura`, exposed via `morsel-size`).
7. Call `exec-run` with the plan and morsel size. Internally `exec-run`:
   - Initializes a `rowbuf` per op.
   - For each tick (until all buffers drained into `sink`):
     - For each fragment whose ready ops have data: pull a morsel from child, run the operator's emit fn, push to parent buffer.
     - Aggregate/sink operators are treated as breakers → they fully drain their child buffer before producing output.
8. Call `report-format` → produces the 15-line alist.
9. Print every `KEY=value` line via `display` + `newline` in the exact order in §2.

The numbers `1024 / 512 / 512 / 256 / 8 / 8` come from real propagation through the operator chain — see §5.

---

## 5. Anti-hardcode

`main.aura` **must not** simply `display` the literal strings from §2. Verification:

- `DAG_NODES` = `(length (plan-nodes plan))` — derived from `plan-build`'s output.
- `DAG_EDGES` = `(length (plan-edges plan))` — derived, not literal.
- `DAG_CYCLES` = `(if (toposort-detect-cycle …) 1 0)` — derived.
- `DAG_TOPSORT` = `(join "," (toposort …))` — derived from toposort output.
- `DAG_BREAKERS` = `(join "," (filter breaker? kinds))` — derived from `breaker?` API.
- `DAG_FRAGMENTS` = `(fragment-count (fragment-build …))` — derived.
- `DAG_MORSEL_SIZE` = `(morsel-size)` — comes from `morsel.aura`.
- `DAG_TICKS`, `DAG_ROWS_*`, `PLAN_VALID` all come from `metrics-snapshot` and `plan-valid?`.

If a contributor replaces any operator body in `scan_op.aura`/`filter_op.aura`/`join_op.aura`/`exec.aura`, the row counts and tick count must change accordingly — the executor genuinely computes them. For example, doubling `scan-emit`'s `n` must double `DAG_ROWS_SCAN` and cascade through downstream keys.

---

## 6. How to run

```sh
aura op.aura \
     plan.aura \
     toposort.aura \
     breaker.aura \
     fragment.aura \
     morsel.aura \
     rowbuf.aura \
     exec.aura \
     sched.aura \
     metrics.aura \
     report.aura \
     scan_op.aura \
     filter_op.aura \
     join_op.aura \
     main.aura
json dogfood
{
  "files": [
    "op.aura",
    "plan.aura",
    "toposort.aura",
    "breaker.aura",
    "fragment.aura",
    "morsel.aura",
    "rowbuf.aura",
    "exec.aura",
    "sched.aura",
    "metrics.aura",
    "report.aura",
    "scan_op.aura",
    "filter_op.aura",
    "join_op.aura",
    "main.aura"
  ],
  "entry": "main.aura",
  "run_mode": "cli_multi",
  "expect_keys": [
    "DAG_NODES",
    "DAG_EDGES",
    "DAG_CYCLES",
    "DAG_TOPSORT",
    "DAG_BREAKERS",
    "DAG_FRAGMENTS",
    "DAG_MORSEL_SIZE",
    "DAG_TICKS",
    "DAG_ROWS_SCAN",
    "DAG_ROWS_FILTERED",
    "DAG_ROWS_PROJECTED",
    "DAG_ROWS_JOINED",
    "DAG_ROWS_AGGREGATED",
    "DAG_ROWS_SUNK",
    "PLAN_VALID"
  ],
  "source_res": [
    "\\(define\\s+\\(op-make\\b",
    "\\(define\\s+\\(op-name\\b",
    "\\(define\\s+\\(op-kind\\b",
    "\\(define\\s+\\(op-inputs\\b",
    "\\(define\\s+\\(op-rows\\b",
    "\\(define\\s+\\(op-add-rows!\\b",
    "\\(define\\s+\\(plan-build\\b",
    "\\(define\\s+\\(plan-nodes\\b",
    "\\(define\\s+\\(plan-edges\\b",
    "\\(define\\s+\\(plan-valid\\?\\b",
    "\\(define\\s+\\(toposort\\b",
    "\\(define\\s+\\(toposort-detect-cycle\\b",
    "\\(define\\s+\\(breaker\\?\\b",
    "\\(define\\s+\\(breaker-kinds\\b",
    "\\(define\\s+\\(fragment-build\\b",
    "\\(define\\s+\\(fragment-count\\b",
    "\\(define\\s+\\(morsel-size\\b",
    "\\(define\\s+\\(morsel-slice\\b",
    "\\(define\\s+\\(rowbuf-new\\b",
    "\\(define\\s+\\(rowbuf-push!\\b",
    "\\(define\\s+\\(rowbuf-drain!\\b",
    "\\(define\\s+\\(rowbuf-count\\b",
    "\\(define\\s+\\(exec-run\\b",
    "\\(define\\s+\\(sched-step\\b",
    "\\(define\\s+\\(sched-ready\\?\\b",
    "\\(define\\s+\\(metrics-init\\b",
    "\\(define\\s+\\(metrics-tick!\\b",
    "\\(define\\s+\\(metrics-record!\\b",
    "\\(define\\s+\\(metrics-snapshot\\b",
    "\\(define\\s+\\(report-format\\b",
    "\\(define\\s+\\(scan-emit\\b",
    "\\(define\\s+\\(filter-emit\\b",
    "\\(define\\s+\\(join-emit\\b"
  ]
}
```
