# Search Insert Position

## Problem

You are given a **sorted** array of distinct integers `nums` and an integer `target`.

Return the index `i` such that:
- If `target` exists in `nums`, return the index where it is located.
- Otherwise, return the index at which `target` would be inserted to keep `nums` sorted in ascending order.

The algorithm must run in **O(log n)** time.

## Function Signature

```python
def solve(nums: list[int], target: int) -> int:
    ...
```

## Input / Output Convention

The harness invokes `solve(nums, target)` directly (no stdin). The examples below show the mapping used by the test harness.

- `CASE0=([1,3,5,6], 5)` → `2`
- `CASE1=([1,3,5,6], 2)` → `1`
- `CASE2=([1,3,5,6], 7)` → `4`
- `CASE3=([1,3,5,6], 0)` → `0`
- `CASE4=([1], 0)` → `0`

## Notes

- `nums` is guaranteed to be sorted in strictly ascending order with all elements distinct.
- The result is always a valid index in `[0, len(nums)]` (it may equal `len(nums)` when `target` is greater than every element).
- Prefer a classic binary-search formulation; a clean `bisect_left`-style approach also satisfies the constraints.
