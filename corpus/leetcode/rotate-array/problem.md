# Rotate Array

## Problem

Given an array `nums` and an integer `k`, rotate the array to the right by `k` steps **in-place**. Rotating right by one step means the last element moves to the front, and every other element shifts one position to the right.

You must modify `nums` directly. Returning a new array is not allowed (for languages where `solve` receives a mutable container, mutate it; otherwise return the rotated array).

When `k` is larger than `n = len(nums)`, only `k mod n` effective rotations are performed.

## Function Signature

```python
def solve(nums: list[int], k: int) -> None:
    ...
```

In languages without `None` returns, the harness will use the returned value.

## Input / Output Convention

The harness reads `CASE0` lines from a JSON-like block. Each case provides:

- `nums`: a list of integers
- `k`: a non-negative integer

and expects the rotated array as the result.

Example:

```
CASE0 = {
    "nums": [1, 2, 3, 4, 5, 6, 7],
    "k":    3
}
# expected -> [5, 6, 7, 1, 2, 3, 4]
```

```
CASE1 = {
    "nums": [-1, -100, 3, 99],
    "k":    2
}
# expected -> [3, 99, -1, -100]
```

## Notes

- `k` may be 0 or larger than `len(nums)` — normalize it with `k %= n` first.
- An in-place solution using the classic three-reverse trick runs in **O(n)** time and **O(1)** extra space.
- Empty input lists and single-element lists should be returned unchanged.
