# Two Sum II - Input Array Is Sorted

## Problem

Given a **1-indexed** array `numbers` that is already sorted in non-decreasing order, find two numbers such that they add up to a specific `target` number. Return the **1-indexed** positions of the two numbers as a list `[i, j]` where `i < j`.

Each input has **exactly one solution**, and you may not use the same element twice.

## Function Signature

```python
def solve(numbers: list[int], target: int) -> list[int]:
    ...
```

## Input / Output Convention

The harness feeds the function directly (no stdin). For local testing, use the `CASE0=...` style:

```
CASE0=[[2,7,11,15], 9] -> [1,2]
CASE1=[[2,3,4], 6] -> [1,3]
CASE2=[[-1,0], -1] -> [1,2]
```

Each case is a list `[numbers, target]` passed positionally to `solve`.

## Notes

- The array is **sorted**, so aim for an `O(n)` solution using two pointers (one at the start, one at the end) rather than the `O(n)` hash-map approach from the classic Two Sum.
- Remember to return **1-indexed** positions, not 0-indexed.
- Since the array can contain negative numbers, do not assume all values are positive.
