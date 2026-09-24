# Minimum Operations to Reduce X to Zero

You are given an array of integers `nums` and an integer `x`. In one operation, you may remove either the **leftmost** (prefix) or the **rightmost** (suffix) element of the current array. Each removal reduces the running sum of removed elements.

Return the **minimum number of operations** required so that the sum of removed elements equals exactly `x`. If it is impossible, return `-1`.

## Function Signature

```python
def solve(nums: list[int], x: int) -> int:
    ...
```

## Input / Output Convention

The harness feeds the function directly (no stdin). For local testing, problems in this set expose a `CASE0=...` block via environment-style lines, e.g.:

```
CASE0=nums=[1,1,3,2,4]; x=5
CASE1=nums=[5,6,7,8,9]; x=4
CASE2=nums=[3,2,20,1,1,3]; x=10
```

Expected outputs:

```
CASE0 -> 2      # remove 1 (left) and 4 (right) or 3+2 (left), etc.
CASE1 -> -1
CASE2 -> 5
```

## Notes

- A classic equivalent viewpoint: removing a prefix + suffix of total sum `x` is the same as finding the **longest subarray** (contiguous middle segment) whose sum equals `total - x`. The answer is then `n - max_len` if such a subarray exists, otherwise `-1`.
- A single-pass **sliding window** (since all numbers are non-negative) solves the subarray variant efficiently in `O(n)`.
- Edge cases to handle: empty `nums`, `x == 0` (answer `0`), `x > total_sum` (answer `-1`), and all elements equal (entire array removed).
