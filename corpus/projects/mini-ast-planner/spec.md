```markdown
# AST-Based Query Planner

A tiny cost-based query planner written in Aura. The planner accepts a logical
operator tree (scan / filter / project / join / aggregate / sort / limit),
rewrites it (filter pushdown, partition pruning, projection pruning), then
emits a physical plan annotated with estimated cost and row counts over a
typed in-memory mini-catalog.

The implementation is deliberately small: a tokenizer for the query DSL, an
S-expression parser that produces a logical AST, a typed catalog of tables
and partitions, a cost model, a rewriter, and a physical-plan emitter. All
state lives in association lists; no records, no vectors.

## 1. Stdout contract (exact order)

The scenario prints exactly the following 12 `KEY=value` lines to stdout, in
this order. The values are computed by the modules at runtime — main.aura
prints them after invoking the planner APIs.



## 2. Module table

| File | Required exported `define` forms |
|------|----------------------------------|
| `catalog.aura` | `(api catalog-tables)` `(api catalog-partitions catalog)` `(api catalog-stats catalog table)` `(api catalog-find-table catalog name)` |
| `tokenize.aura` | `(api tokenize text)` `(api token-kind? tok k)` |
| `parse.aura` | `(api parse-query toks)` `(api ast-kind? node k)` `(api ast-fields node)` |
| `rewrite.aura` | `(api rewrite-pushdown-filters ast catalog)` `(api rewrite-prune-partitions ast catalog)` `(api rewrite-prune-projections ast)` `(api rewrite-count-filters orig rewritten)` |
| `cost.aura` | `(api cost-estimate ast catalog)` `(api cost-rows ast)` `(api cost-model-name)` |
| `plan.aura` | `(api plan-build ast catalog)` `(api plan-root plan)` `(api plan-kind plan)` `(api plan-scan-count plan)` `(api plan-join-count plan)` |
| `types.aura` | `(api type-of row-class)` `(api type-compat? a b)` |
| `emit.aura` | `(api emit-physical plan)` `(api emit-root op)` |
| `stats.aura` | `(api stats-rowcount stats)` `(api stats-selectivity stats)` |
| `ops.aura` | `(api op-make-scan table)` `(api op-make-filter name kids)` `(api op-make-project cols kids)` `(api op-make-join kind left right)` `(api op-make-agg fns kids)` `(api op-make-sort keys kids)` `(api op-make-limit n kids)` `(api op-fields op)` `(api op-kind op)` |
| `pretty.aura` | `(api pretty-op op)` `(api pretty-plan plan)` |
| `errors.aura` | `(api error-make code msg)` `(api error-format err)` |
| `main.aura` | `(api run-scenario)` (and top-level call) |

## 3. Scenario steps executed by `main.aura`

1. Build the in-memory catalog via `catalog-tables`, `catalog-partitions`,
   `catalog-stats` (tables: `orders`, `customers`, `lineitems`, `regions`;
   partitions carry per-partition row counts).
2. Run the tokenizer + parser on a sample DSL query string
   (`SELECT name, total FROM orders JOIN customers ON orders.cid = customers.id
   WHERE region = 'eu' AND total > 100 ORDER BY total DESC LIMIT 50`)
   using `tokenize` and `parse-query` to obtain the logical AST.
3. Rewrite via `rewrite-pushdown-filters`, `rewrite-prune-partitions`,
   `rewrite-prune-projections`; record counts with
   `rewrite-count-filters`.
4. Estimate cost and row counts via `cost-estimate` / `cost-rows`.
5. Build the physical plan with `plan-build`; inspect root/kind/scan/join
   counts via `plan-root`, `plan-kind`, `plan-scan-count`,
   `plan-join-count`.
6. Emit a physical string via `emit-physical`.
7. Print all 12 `KEY=value` lines in the exact order above.

## 4. Anti-hardcode guard

`main.aura` must drive every printed value from a module API:

- `REWRITE.filters_pushed` ← `(rewrite-count-filters orig rewritten)`
- `REWRITE.partitions_pruned` ← difference of partition lists returned by
  `rewrite-prune-partitions`
- `REWRITE.projections_pruned` ← field-set delta from
  `rewrite-prune-projections`
- `PLAN.cost`, `PLAN.rows` ← `(cost-estimate ast catalog)`, `(cost-rows ast)`
- `PLAN.root`, `PLAN.kind` ← `(plan-root plan)`, `(plan-kind plan)`
- `CATALOG.tables`, `CATALOG.partitions` ← `(catalog-tables)`,
  `(catalog-partitions catalog)`
- `EMIT.scan_count`, `EMIT.join_count` ← `(plan-scan-count plan)`,
  `(plan-join-count plan)`
- `COST.model` ← `(cost-model-name)`

A solution that prints the literal strings without invoking these APIs will
fail the grader.

## 5. How to run



The invocation loads every module into a shared top-level, runs
`(run-scenario)` from `main.aura`, and prints the 12 `KEY=value` lines.
json dogfood
{
  "files": [
    "catalog.aura",
    "tokenize.aura",
    "parse.aura",
    "rewrite.aura",
    "cost.aura",
    "plan.aura",
    "types.aura",
    "emit.aura",
    "stats.aura",
    "ops.aura",
    "pretty.aura",
    "errors.aura",
    "main.aura"
  ],
  "entry": "main.aura",
  "run_mode": "cli_multi",
  "expect_keys": [
    "PLAN.kind",
    "PLAN.root",
    "PLAN.cost",
    "PLAN.rows",
    "REWRITE.filters_pushed",
    "REWRITE.partitions_pruned",
    "REWRITE.projections_pruned",
    "CATALOG.tables",
    "CATALOG.partitions",
    "COST.model",
    "EMIT.scan_count",
    "EMIT.join_count"
  ],
  "source_res": [
    "\\(define\\s+\\(api\\s+catalog-tables\\b",
    "\\(define\\s+\\(api\\s+catalog-partitions\\b",
    "\\(define\\s+\\(api\\s+catalog-stats\\b",
    "\\(define\\s+\\(api\\s+catalog-find-table\\b",
    "\\(define\\s+\\(api\\s+tokenize\\b",
    "\\(define\\s+\\(api\\s+token-kind\\?\\b",
    "\\(define\\s+\\(api\\s+parse-query\\b",
    "\\(define\\s+\\(api\\s+ast-kind\\?\\b",
    "\\(define\\s+\\(api\\s+ast-fields\\b",
    "\\(define\\s+\\(api\\s+rewrite-pushdown-filters\\b",
    "\\(define\\s+\\(api\\s+rewrite-prune-partitions\\b",
    "\\(define\\s+\\(api\\s+rewrite-prune-projections\\b",
    "\\(define\\s+\\(api\\s+rewrite-count-filters\\b",
    "\\(define\\s+\\(api\\s+cost-estimate\\b",
    "\\(define\\s+\\(api\\s+cost-rows\\b",
    "\\(define\\s+\\(api\\s+cost-model-name\\b",
    "\\(define\\s+\\(api\\s+plan-build\\b",
    "\\(define\\s+\\(api\\s+plan-root\\b",
    "\\(define\\s+\\(api\\s+plan-kind\\b",
    "\\(define\\s+\\(api\\s+plan-scan-count\\b",
    "\\(define\\s+\\(api\\s+plan-join-count\\b",
    "\\(define\\s+\\(api\\s+type-of\\b",
    "\\(define\\s+\\(api\\s+type-compat\\?\\b",
    "\\(define\\s+\\(api\\s+emit-physical\\b",
    "\\(define\\s+\\(api\\s+emit-root\\b",
    "\\(define\\s+\\(api\\s+stats-rowcount\\b",
    "\\(define\\s+\\(api\\s+stats-selectivity\\b",
    "\\(define\\s+\\(api\\s+op-make-scan\\b",
    "\\(define\\s+\\(api\\s+op-make-filter\\b",
    "\\(define\\s+\\(api\\s+op-make-project\\b",
    "\\(define\\s+\\(api\\s+op-make-join\\b",
    "\\(define\\s+\\(api\\s+op-make-agg\\b",
    "\\(define\\s+\\(api\\s+op-make-sort\\b",
    "\\(define\\s+\\(api\\s+op-make-limit\\b",
    "\\(define\\s+\\(api\\s+op-fields\\b",
    "\\(define\\s+\\(api\\s+op-kind\\b",
    "\\(define\\s+\\(api\\s+pretty-op\\b",
    "\\(define\\s+\\(api\\s+pretty-plan\\b",
    "\\(define\\s+\\(api\\s+error-make\\b",
    "\\(define\\s+\\(api\\s+error-format\\b",
    "\\(define\\s+\\(api\\s+run-scenario\\b"
  ]
}
```
