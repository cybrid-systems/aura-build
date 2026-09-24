# Count of Smaller Numbers After Self

## Problem

You are given an integer array `nums`. For each index `i` (0-based), count how many numbers in `nums` that appear **strictly after** position `i` are **strictly smaller** than `nums[i]`. Return the list of counts in the original order.

Formally, for every `i`, compute:

```
counts[i] = |{ j : j > i and nums[j] < nums[i] }|
```

## Function Signature

```python
def solve(nums: List[int]) -> List[int]:
    ...
```

## Input / Output Convention

The harness invokes `solve(nums)` directly (no stdin). A sample case is shown below as documentation only — your function should accept a plain list of ints and return a list of ints.

```
CASE0_IN = [5, 2, 6, 1]
CASE0_OUT = [2, 1, 1, 0]

CASE1_IN = [-1]
CASE1_OUT = [0]

CASE2_IN = [-1, -1]
CASE2_OUT = [0, 0]
```

## Notes

- `nums` may contain negative numbers and duplicates; duplicates are **not** counted (the comparison is *strictly smaller*).
- A single element has count `0`.
- Expected time complexity is `O(n log n)` — a binary indexed tree (Fenwick tree) over a coordinate-compressed domain, or a modified mergesort, are both acceptable approaches.
