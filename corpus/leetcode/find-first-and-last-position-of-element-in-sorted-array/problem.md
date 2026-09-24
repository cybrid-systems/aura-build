# Find First and Last Position of Element in Sorted Array

## Problem

Given a sorted (non-decreasing) integer array `a` of length `n` and an integer `target`, return the **first** and **last** index at which `target` occurs in `a`. If `target` is not present, return `-1` for both values.

You must achieve **O(log n)** time complexity.

## Function Signature

```lisp
(defun solve (a target)
  ;; returns cons cell (first . last)
  ;; returns (-1 . -1) when target not found
  )
```

- `a` — list of integers, sorted in non-decreasing order.
- `target` — integer to search for.
- Returns a pair `(first . last)` of indices (0-based), or `(-1 . -1)` if absent.

## Input / Output Convention

Each test case is provided on consecutive lines as `CASE0=...` pairs:

```
CASE0=A=(5,7,7,8,8,10)
CASE0=T=8
CASE1=A=(5,7,7,8,8,10)
CASE1=T=6
```

For every group, the harness reads one `A=` line and one `T=` line, then calls `solve` with the parsed list and the integer `target`. The returned pair is compared against the expected `(first . last)`.

**Example trace:**

- `A=(5,7,7,8,8,10)`, `T=8` → expected `(3 . 4)`
- `A=(5,7,7,8,8,10)`, `T=6` → expected `(-1 . -1)`
- `A=(1)`, `T=1` → expected `(0 . 0)`

## Notes

- Two independent binary searches are sufficient: one biased to find the leftmost occurrence, one biased to find the rightmost occurrence.
- Watch the termination condition carefully — the standard `lo <= hi` pattern must be adapted so the search collapses to a single index rather than terminating early.
- Indices are 0-based; when `target` exists exactly once, both values are equal.
- `a` may be empty; in that case the answer is always `(-1 . -1)`.
