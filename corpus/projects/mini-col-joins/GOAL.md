# Columnar Nested-Loop Join — Mini-Col-Joins

An in-memory column-store toy that demonstrates an *adaptive* nested-loop join. Three strategies compete for every join:

- **naive** — page-by-page cartesian scan of two column vectors
- **index-nested** — build a hash-bucket index on the build side, probe with the probe side
- **block-nested** — chunk the outer side into a fixed-size block, reuse one index per chunk

The optimizer looks at runtime cardinality feedback (build distinct count, probe length, threshold `K`) and picks the cheapest strategy, then prints a uniform `KEY=value` contract.

---

## 1. Stdout contract (exact order)



13 keys. Lines must appear in this order. Values for the last 7 are computed at runtime from the column data; we deliberately do not pre-bake them.

---

## 2. Module table

| # | File | Required exported `define` forms |
|---|------|----------------------------------|
| 1 | `src/util/list_util.aura` | `(api car*), (api cdr*), (api length lst)`, `(api sum lst)`, `(api filter pred lst)`, `(api assoc* k alist)` |
| 2 | `src/col/column.aura` | `(api make-column name vals)`, `(api col-name c)`, `(api col-vals c)`, `(api col-len c)` |
| 3 | `src/catalog/catalog.aura` | `(api register-rel! name cols)`, `(api get-rel name)`, `(api list-rels)` |
| 4 | `src/col/stats.aura` | `(api distinct-count vals)`, `(api min-cost stats)` |
| 5 | `src/catalog/columns_meta.aura` | `(api col-distinct rel col)` |
| 6 | `src/join/row.aura` | `(api make-row cols vs)`, `(api row-cols r)`, `(api row-vals r)`, `(api row-get r col)` |
| 7 | `src/join/result.aura` | `(api result-len rs)`, `(api result-nth rs i)`, `(api result-rows rs)`, `(api first-match-row rs)` |
| 8 | `src/join/strategies.aura` | `(api naive-join L R lcol rcol)`, `(api index-join L R lcol rcol)`, `(api block-join L R lcol rcol k)` |
| 9 | `src/join/cost_model.aura` | `(api cost-naive L R)`, `(api cost-index L R)`, `(api cost-block L R k)`, `(api choose-strategy stats k)` |
| 10 | `src/join/optimizer.aura` | `(api plan-join left right lcol rcol k)`, `(api explain-plan p)` |
| 11 | `main.aura` | driver + printer |

---

## 3. Scenario steps (`main.aura`)

1. Build two columns in memory via `make-column`:
   - `orders`:  `[orders.id=(1 2 3 4 5 6 7 8) orders.customer_id=(3 1 2 2 3 4 1 5)]` ⇒ rows=8
   - `customers`: `[customers.id=(1 2 3 4 5 6) customers.name=(A B C D E F)]` ⇒ rows=6
2. `register-rel!` both, `get-rel` them back, derive `ROWS_LEFT`/`ROWS_RIGHT` from `col-len`.
3. Feed the columns into `cost-naive`, `cost-index`, `cost-block` (block size `2`) and print `COST_*`.
4. `distinct-count` of build side → `BUILD_DISTINCT`; probe side length → `PROBE_LEN`.
5. `choose-strategy` with `K=4` threshold → `CHOSEN=block_nested` (index would also beat naive but block size matches cache hint).
6. `plan-join` builds the execution plan; `explain-plan` returns a description string (printed via `display` only when verbose, not counted).
7. Run the chosen strategy by dispatching on the plan symbol (naive / index / block) — emits a `result`.
8. `first-match-row` picks the winning row where `customer_id=2`; resolve `id=2 → name=Bob` via a fresh column lookup so `WINNER` is genuinely computed.
9. Walk `result-len` / `result-nth` to confirm we didn't fabricate.

---

## 4. Anti-hardcode guard

- `COST_NAIVE`, `COST_INDEX`, `COST_BLOCK` come from `cost-model`, not literals.
- `BUILD_DISTINCT` is the runtime `distinct-count` of `customers.id`.
- `CHOSEN` is the symbol returned by `choose-strategy`, not a quoted constant in `display`.
- `WINNER` is built by `row-get` + a `customers` lookup; flipping any row in any column changes the printed value.
- A run that skips every API call (only prints the contract literal) will fail the verifier's cost-equality and result-traversal checks.

---

## 5. How to run

```bash
aura src/util/list_util.aura \
     src/col/column.aura \
     src/catalog/catalog.aura \
     src/catalog/columns_meta.aura \
     src/col/stats.aura \
     src/join/row.aura \
     src/join/result.aura \
     src/join/strategies.aura \
     src/join/cost_model.aura \
     src/join/optimizer.aura \
     main.aura
json dogfood
{"files":["src/util/list_util.aura","src/col/column.aura","src/catalog/catalog.aura","src/catalog/columns_meta.aura","src/col/stats.aura","src/join/row.aura","src/join/result.aura","src/join/strategies.aura","src/join/cost_model.aura","src/join/optimizer.aura","main.aura"],"entry":"main.aura","run_mode":"cli_multi","expect_keys":["JOB_ID","JOIN_TYPE","LEFT_REL","RIGHT_REL","LEFT_COL","RIGHT_COL","ROWS_LEFT","ROWS_RIGHT","CHOSEN","BLOCK_SIZE","BUILD_DISTINCT","PROBE_LEN","COST_NAIVE","COST_INDEX","COST_BLOCK","WINNER"],"source_res":["\\(define\\s+\\(api\\s+car\\*","\\(define\\s+\\(api\\s+make-column","\\(define\\s+\\(api\\s+register-rel!","\\(define\\s+\\(api\\s+col-distinct","\\(define\\s+\\(api\\s+distinct-count","\\(define\\s+\\(api\\s+make-row","\\(define\\s+\\(api\\s+first-match-row","\\(define\\s+\\(api\\s+naive-join","\\(define\\s+\\(api\\s+index-join","\\(define\\s+\\(api\\s+block-join","\\(define\\s+\\(api\\s+cost-naive","\\(define\\s+\\(api\\s+cost-index","\\(define\\s+\\(api\\s+choose-strategy","\\(define\\s+\\(api\\s+plan-join"]}
```
