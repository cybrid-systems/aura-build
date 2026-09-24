# Longest Subarray with Sum at Most K

## Problem

Given an array of integers `nums` and an integer `k`, find the length of the longest contiguous subarray whose sum is **less than or equal to** `k`.

If no such subarray exists, return `0`.

All numbers in `nums` are non-negative.

## Function Signature

```lisp
(defun solve (nums k)
  ;; returns the length of the longest contiguous subarray
  ;; with sum <= k
  )
```

## Input

The harness provides input via `CASE0=...` style lines. Each test case supplies:

- `CASE0=NUMS=<comma-separated-integers>`
- `CASE0=K=<integer>`

For example:

```
CASE0=NUMS=1,2,3,4,5
CASE0=K=8
```

## Output

Print a single integer per test case: the maximum length of a contiguous subarray with sum at most `k`.

## Notes

- Since all numbers are non-negative, a sliding-window (two-pointer) approach runs in O(n) time.
- Watch the boundary when no valid subarray exists (e.g., when `k < 0` or the array is empty).
- The subarray must be contiguous; subsequences are not allowed.
