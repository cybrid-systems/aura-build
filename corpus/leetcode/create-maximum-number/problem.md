# Create Maximum Number

## Problem

You are given two integer arrays `nums1` and `nums2` of digits (each digit is between `0` and `9`) and an integer `k`. From `nums1` you must pick exactly `i` digits and from `nums2` exactly `k - i` digits for some `i` in `[0, k]`, preserving the original relative order of digits inside each array. Concatenate the two chosen subsequences to form a length-`k` number, and return the **maximum** such number as an array of digits (most significant digit first).

If two numbers of length `k` are compared lexicographically, the larger one wins.

## Function Signature

```python
def solve(nums1: list[int], nums2: list[int], k: int) -> list[int]:
    ...
```

## Input / Output Convention

The harness drives the solver directly (no stdin). A typical case looks like:

```
CASE0=([3,4,6,5], [9,1,2,5,8,3], 5)
CASE1=([6,7], [6,0,4], 5)
CASE2=([3,9], [8,9], 3)
```

For each case, the solver receives the parsed arguments and must return a list of `k` digits representing the lexicographically largest attainable number.

## Notes

- `len(nums1) + len(nums2) >= k` is guaranteed; otherwise no solution exists (this case does not appear in the tests).
- A single combined subproblem is *pick the max subsequence of length `t` from one array while preserving order* — solve it greedily with a monotone stack in `O(n)`.
- The full solution enumerates `i` from `max(0, k - len(nums2))` to `min(k, len(nums1))`, merges the two picks via a custom max-merge, and keeps the best result. Overall complexity is `O(k * (len(nums1) + len(nums2)))`.
- Return the result as a plain `list[int]`; the harness will compare it to the expected answer element-wise.
