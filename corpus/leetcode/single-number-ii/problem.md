# Single Number II

## Problem

You are given an integer array `nums` where every element appears **exactly three times** except for one element which appears **exactly once**. Return the element that appears exactly once.

You must implement a solution that runs in `O(n)` time and uses `O(1)` extra space (excluding the input array).

## Function Signature

```python
def solve(nums: list[int]) -> int:
    ...
```

## Input / Output Convention

Input is supplied via standard input as a series of `CASE0=...` lines, one per test case. Each line is a single space-separated list of integers representing `nums`.

Output one line per test case with the integer that appears exactly once.

Example:

```
CASE0=2 2 3 2
CASE1=0 1 0 1 0 1 99
CASE2=-5 -5 -5 -3
```

Expected output:

```
3
99
-3
```

## Notes

- `len(nums) >= 1` and fits the constraints so a unique single element is guaranteed to exist.
- The array length is of the form `3k + 1` for some `k >= 0`.
- Bitwise / counting approaches (tracking per-bit counts modulo 3) are the intended path; a hash map also works but will not satisfy the `O(1)` extra-space requirement.
