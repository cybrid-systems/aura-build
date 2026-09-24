# Number of Subarrays with Bounded Maximum

## Problem Statement

You are given an integer array `nums` and two integers `left` and `right`.

Your task is to return the number of contiguous (non-empty) subarrays such that the **maximum element** of the subarray lies in the inclusive range `[left, right]`.

Formally, for a subarray `nums[i..j]`, let `M = max(nums[i], nums[i+1], ..., nums[j])`. Count all pairs `(i, j)` with `i ≤ j` such that `left ≤ M ≤ right`.

## Function Signature

```python
def solve(nums: list[int], left: int, right: int) -> int:
    ...
```

## Input / Output Convention (Aura Harness)

The harness reads a single test case from a bound global dictionary. Your function receives the parsed values directly as arguments.

For local sanity checks, the same data is mirrored in `CASE0` as a labeled block:

```
CASE0 = {
    "nums":  [2, 1, 4, 3],
    "left":  2,
    "right": 3,
    "answer": 3,
}
```

Explanation of `CASE0`: the subarrays with maximum in `[2, 3]` are `[2]`, `[2, 1]`, and `[3]`.

## Notes

- `nums` may contain both positive and negative integers; length is at least 1.
- A clean approach uses a sliding window: track the most recent index where a value exceeds `right` (which **resets** the window) and the most recent index where a value falls in `[left, right]` (which **extends** the valid count). The answer is the sum over positions of `(last_in_range - last_too_big)`.
- The result fits in a 64-bit signed integer.
- Expected complexity: **O(n)** time, **O(1)** extra space.
