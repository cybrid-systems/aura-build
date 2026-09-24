# Maximum Subarray

## Problem

Given an integer array `nums` (may contain negative numbers), find the contiguous subarray (containing at least one element) that has the largest sum, and return that sum.

## Function Signature

```python
def solve(nums: list[int]) -> int:
    ...
```

## Input / Output Convention

The harness reads lines in the following `CASE0=...` format. The first line names the case; subsequent lines provide inputs.

```
CASE0=
1 -2 3 -1 2 -1 5 -4
```

- The `CASE0=` header indicates the start of a test case.
- The remaining non-empty line contains space-separated integers representing the array `nums`.

Output: a single integer printed on its own line — the maximum subarray sum.

## Notes

- The array has length `n` where `1 <= n <= 10^5`, and each element satisfies `-10^4 <= nums[i] <= 10^4`.
- An efficient linear-time solution (Kadane's algorithm) is expected; an `O(n^2)` or worse approach may time out on large inputs.
- If all numbers are negative, the answer is the single largest (least negative) element.
