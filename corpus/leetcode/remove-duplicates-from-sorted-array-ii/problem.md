# Remove Duplicates from Sorted Array II

## Problem

Given an integer array `nums` sorted in non-decreasing order, modify it **in-place** so that each unique element appears **at most twice**. The relative order of the elements must be kept the same.

Return the length `k` of the array after the modification. The first `k` entries of `nums` should contain the resulting array; their contents beyond index `k` do not matter.

This is the "allow up to two duplicates" variant of the classic remove-duplicates task.

## Function Signature

```python
def solve(nums: list[int]) -> int:
    ...
```

## Input / Output Convention (stdin-less Aura harness)

The harness calls `solve(nums)` directly. The examples below show the
`CASE0=...` line format used by the test runner; embed the array as a
Python list literal.

```
CASE0={"nums": [1,1,1,2,2,3]} -> 5
CASE1={"nums": [0,0,1,1,1,1,2,3,3]} -> 7
```

The arrow `->` separates the input `dict` from the expected return value
`k`. After the call, the first `k` elements of `nums` must match the
expected deduplicated prefix (in order); trailing elements are ignored.

## Notes

- Must operate **in-place** with **O(1)** extra space — do not allocate
  a new array.
- The array is already sorted, so use a slow/fast two-pointer pattern:
  the slow pointer tracks the write position for the allowed prefix.
- A simple rule that works: an element at index `i` may overwrite the
  position pointed to by the slow pointer if it has appeared fewer than
  two times already in the prefix (`i - slow < 2` is insufficient on its
  own — compare against the element two slots back in the prefix).
- Expected answers for the cases above:
  - `[1,1,1,2,2,3]` → length `5`, prefix `[1,1,2,2,3]`.
  - `[0,0,1,1,1,1,2,3,3]` → length `7`, prefix `[0,0,1,1,2,3,3]`.
