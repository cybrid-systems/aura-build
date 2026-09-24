# Minimum Interval to Include Each Query

## Problem

You are given a set of **intervals** on the number line and a set of **queries** (points). For each query point `q`, report the length of the **smallest** interval (minimum number of integers it contains) that covers `q`. If no interval covers the query, the answer for that query is `-1`.

Each interval `[l, r]` is inclusive on both ends, and its size is `r - l + 1`.

## Function Signature

```clojure
(solve [intervals queries] ...)
```

- `intervals` — a vector of `[l r]` pairs (integers, `l <= r`).
- `queries`  — a vector of integers.
- Returns a vector of the same length as `queries`, where the `i`-th element is the size of the smallest interval containing `queries[i]`, or `-1` if none does.

## Input / Output Convention (Aura harness)

The harness does not read from `stdin`. Input is provided via the global **`CASE0`** constant, formatted as:

```
CASE0=[ [[1 4] [2 8] [3 6] [4 8]], [3 4 5 6 7 8] ]
```

That is: `CASE0` is bound to a single value containing the function arguments in order — first `intervals`, then `queries`. Your `solve` function should use `CASE0` (or its destructured form) as its source of data.

Output is the value returned by `solve`, typically printed by the harness for inspection.

## Notes

- Sort both `intervals` and `queries` for an efficient sweep, but remember to restore the original query order in the output.
- For each query, only consider intervals whose left endpoint is `<= q`; among those, keep the one with the smallest right endpoint (and therefore the smallest length covering `q`).
- Time complexity `O((n + q) log(n + q))` using a min-heap keyed by right endpoint is the typical approach.
- Distinguish “no covering interval” (`-1`) from “size 1” (a single-point interval `[q q]`).
