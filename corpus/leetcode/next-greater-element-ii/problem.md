# Next Greater Element II

## Problem

Given a circular integer array `nums` (i.e., the element after the last element is the first element), for each index `i` find the **next greater element** with respect to the circular ordering. The next greater element of `nums[i]` is `nums[j]` where `j` is the smallest index such that:

- `j != i`,
- moving from `i` to `j` wraps around the end of the array if needed,
- and `nums[j] > nums[i]`.

If no such element exists, the answer for index `i` is `-1`.

Return an array of the same length where each position holds the next greater element for the corresponding index of `nums`.

## Function Signature

```python
def solve(nums: list[int]) -> list[int]:
    ...
```

## Input / Output Convention

The harness does not use stdin/stdout. Instead, each test case is provided as a list argument to `solve`, and the return value is compared against the expected output.

For example, a case may be invoked as:

```
CASE0= [1, 2, 1]
CASE0_EXPECTED = [2, -1, 2]
```

Your function must accept a single argument `nums` (a `list[int]`) and return a `list[int]` containing the next greater element for each position in circular order.

## Notes

- The input array may be empty; in that case, return an empty list.
- Use a **monotonic stack** technique on the array traversed twice (length `2 * n`) to efficiently handle the circular wrap-around in `O(n)` time.
- Do not modify the input list; treat it as read-only.
