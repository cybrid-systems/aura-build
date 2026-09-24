# Max Consecutive Ones II

## Problem

Given a binary array `nums` (each element is `0` or `1`), you may flip **at most one** `0` into a `1`. Return the length of the longest contiguous subarray containing only `1`s after performing the operation.

The subarray must be a single contiguous block; you only choose one (or zero) positions to flip.

## Function Signature

```lisp
(defun solve (nums)
  ;; returns the maximum length as an integer
)
```

## Input / Output (Aura harness, stdin-less)

The harness calls `(solve nums)` directly. No stdin/stdout is used.

Test cases are provided as `CASE0=...` lines in the problem file. Each case assigns a list of integers to `nums`:

```
CASE0 = (1 1 0 1 1 1 0 1 1)
CASE1 = (1 0 1 1 0)
CASE2 = (0 0 0)
CASE3 = (1 1 1 1)
```

Expected behavior:

| Case | Input                              | Output |
|------|------------------------------------|--------|
| 0    | `(1 1 0 1 1 1 0 1 1)`              | `6`    |
| 1    | `(1 0 1 1 0)`                      | `4`    |
| 2    | `(0 0 0)`                          | `1`    |
| 3    | `(1 1 1 1)`                        | `4`    |

## Notes

- Flipping zero `0`s is allowed; flipping is optional.
- A sliding window that keeps at most one `0` inside yields an O(n) solution.
- The window's length is updated whenever expanding is allowed; the answer is the maximum window length seen.
