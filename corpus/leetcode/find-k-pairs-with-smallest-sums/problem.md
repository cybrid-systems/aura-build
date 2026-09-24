# Find K Pairs with Smallest Sums

You are given two integer arrays `nums1` and `nums2`, both sorted in **non-decreasing** order, and an integer `k`. Define a *pair* `(u, v)` as one element taken from `nums1` and one element taken from `nums2`. The *sum* of a pair is `u + v`.

Return the `k` pairs `(u1, v1), (u2, v2), ..., (uk, vk)` with the smallest sums. The result must be sorted in **non-decreasing** order by pair sum, and ties may be broken in any order (returning pairs in any valid ordering is acceptable).

If there are fewer than `k` possible pairs in total, return all of them.

## Function Signature

```python
def solve(nums1: list[int], nums2: list[int], k: int) -> list[tuple[int, int]]:
    ...
```

## Input / Output Convention

This problem is provided as part of a stdin-less harness. The driver invokes `solve(nums1, nums2, k)` directly with Python lists. For local testing with sample data, the harness may also expose a `CASE0` literal of the form:

```
CASE0 = {
    "nums1": [1, 7, 11],
    "nums2": [2, 4, 6],
    "k": 3,
    "expected": [(1, 2), (1, 4), (1, 6)],
}
```

Read from `CASE0` if present, otherwise call `solve(...)` directly.

## Notes

- Both input arrays are sorted ascending; this is essential for the heap-based solution.
- A naive `O(n*m)` exploration is unnecessary; a min-heap seeded with at most `min(k, len(nums1))` candidates from `nums2[0]` suffices, pushing `(sum, i, j)` and popping the smallest while advancing `j`.
- Complexity target: `O(k log k)` time after an `O(min(k, n))` heap build, with `O(min(k, n))` extra space.
- Output is a list of `tuple[int, int]`; do not deduplicate or re-sort beyond what the algorithm naturally produces.
