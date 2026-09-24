# Two Sum Less Than K

## Problem

Given a **sorted** array of integers and an integer `K`, count the number of pairs `(i, j)` with `i < j` such that `A[i] + A[j] < K`.

Your task is to compute this count efficiently.

## Function Signature

```python
def solve(A: list[int], K: int) -> int:
    ...
```

## Input / Output Convention

This is a stdin-less harness. Cases are provided directly to `solve`:

```
CASE0 = {"A": [1, 2, 3, 4, 5], "K": 7}
CASE1 = {"A": [-3, -1, 0, 2, 4], "K": 2}
CASE2 = {"A": [1, 1, 1, 1], "K": 3}
```

For each case, call `solve(A, K)` and return the resulting integer count.

## Notes

- `A` is already sorted in non-decreasing order; you can rely on this.
- Use the two-pointer technique: one pointer at the start, one at the end, and shrink the search space based on the sum.
- Aim for **O(n)** time after sorting (sorting is given, so no extra preprocessing needed).
- All values fit comfortably in standard 32-bit signed integers.
