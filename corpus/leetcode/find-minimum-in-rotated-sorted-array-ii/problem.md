# Find Minimum in Rotated Sorted Array II

## Problem Statement

You are given an array `nums` of length `n` that was originally sorted in **non-decreasing** order, then rotated at some unknown pivot (0 or more positions). The array may now contain **duplicate** values.

Your task is to return the **minimum element** of `nums`.

You must implement the function `solve(nums)` that returns the index of the minimum element. If several indices hold the minimum, returning **any one of them** is acceptable.

You may assume `n >= 1`.

## Function Signature

```python
def solve(nums: list[int]) -> int:
    ...
```

## Input / Output Convention (Aura Harness)

The harness drives interaction through a single `CASE` block read from the configuration. There is **no stdin**; instead the environment sets, for example:

```
CASE0=nums=[1,3,5,7,9]
CASE1=nums=[2,2,2,0,1]
CASE2=nums=[5,5,5,5,5]
CASE3=nums=[3,1,2,3,3]
```

For each case, the framework constructs the `nums` list and calls `solve(nums)`. Your return value is compared against an expected index of the minimum.

## Notes

- The naive `min(nums)` solution is `O(n)` and is allowed, but the intended solution runs in **average O(log n)** using a binary-search style approach that gracefully handles duplicates (e.g., by shrinking the search range when `nums[lo] == nums[hi]`).
- Because of duplicates, the worst case can degrade to `O(n)`, which is acceptable.
- Return any valid index `i` such that `nums[i]` equals the global minimum.
