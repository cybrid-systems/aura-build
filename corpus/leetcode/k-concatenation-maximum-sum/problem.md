# K-Concatenation Maximum Sum

## Problem

You are given an array `a` of length `n` (containing `0`s, positive, and negative integers). Consider forming a new array `b` by concatenating `a` with itself `k` times, i.e., `b = a + a + ... + a` (`k` copies).

Find the maximum possible sum over all contiguous subarrays of `b`. Return this maximum sum modulo `10^9 + 7`.

- If the maximum sum is negative, return `0`.

## Function Signature

```python
def solve(a: list[int], k: int) -> int:
    ...
```

## Input / Output Convention

The harness reads from inline cases, not stdin. Each case is described by two lines:

```
CASE0
<comma-separated integers>          # the array a
<integer k>                          # number of concatenations
```

Example:

```
CASE0
1,-2,1,2,-2,1,-2,1
3
```

Output (one line per case) is the answer for that case.

## Notes

- A classic approach uses Kadane's algorithm twice (once for maximum subarray within one copy, once for maximum prefix / maximum suffix), then combines with `total_sum * (k - 2)` when `total_sum > 0`.
- Return the answer modulo `10^9 + 7`; if the actual maximum sum is negative, return `0`.
- Constraints typically allow `n, k` up to ~`10^5` and values up to ~`10^4`, so the algorithm must run in `O(n)` per case.
