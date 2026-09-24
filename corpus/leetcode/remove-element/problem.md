# Remove Element

## Problem

Given an integer array `nums` and an integer `val`, remove all occurrences of `val` **in-place**. The order of the remaining elements may be changed, but the first `k` elements of `nums` should contain the elements that are not equal to `val`. Return `k`.

You must do this using **O(1)** extra space (the output array itself does not count).

## Function Signature

```clojure
(solve nums val)
```

- `nums` — a vector of integers (you may mutate it freely).
- `val`  — the integer value to remove.
- Returns the new length `k`.

## I/O Convention

Your solution is called by a harness that pre-loads the inputs; there is **no stdin**. Each test case is supplied as `CASE0=` style configuration in the runner, and the function is invoked directly.

Example wiring (for reference only — the harness handles I/O):

```
CASE0={"nums":[3,2,2,3],"val":3}   ; expect result 2
CASE1={"nums":[0,1,2,2,3,0,4,2],"val":2} ; expect result 5
```

After `solve` returns `k`, the first `k` entries of the (mutated) `nums` vector hold the kept values in arbitrary order.

## Notes

- Use a two-pointer approach: one pointer scans forward, another marks the next "keep" slot (or swaps with the tail pointer) to achieve O(n) time and O(1) extra space.
- Elements beyond index `k-1` after the call are not inspected, so they may contain leftover values.
- Relative order of kept elements is **not** required to be preserved.
