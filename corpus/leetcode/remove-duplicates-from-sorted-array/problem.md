# Remove Duplicates from Sorted Array

## Problem

Given an integer array `nums` sorted in non-decreasing order, remove the duplicates **in-place** so that each unique element appears exactly once. The relative order of the unique elements must be preserved.

After removing duplicates, return the number of unique elements, say `k`. The first `k` entries of `nums` should contain the unique elements in their original order. The values beyond index `k - 1` are irrelevant.

You must do this using **O(1)** extra space (the output array is counted as modified in-place, not as extra space).

## Function Signature

```python
def solve(nums: list[int]) -> int:
    # modify nums in-place
    return k
```

- `nums`: the input sorted list of integers (length `n`, `0 ≤ n ≤ 10^5`, values fit in 32-bit signed int).
- Returns: the count `k` of unique elements after the removal.

## Input / Output Convention (Aura harness)

The harness reads no stdin. Instead, each test case is provided as a **CASE0** literal embedded in the source. For example:

```python
CASE0 = {
    "nums": [1, 1, 2, 2, 3, 4, 4],
    "expected_k": 4,
    "expected_first_k": [1, 2, 3, 4],
}
```

Your `solve` function will be invoked with `nums = CASE0["nums"]` (a fresh copy per case). It must return `k`, and the first `k` elements of the modified list must match `expected_first_k`.

## Notes

- The input array is already sorted, which allows a single-pass two-pointer scan.
- Do **not** allocate a second list; mutate `nums` directly.
- The `expected_k` is always equal to `len(expected_first_k)`, and `expected_first_k` is the deduplicated sequence in its original order.
