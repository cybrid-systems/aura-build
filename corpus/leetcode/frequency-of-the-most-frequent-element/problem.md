# Frequency of the Most Frequent Element

## Problem

You are given an integer array `nums` of length `n` and an integer `k`. You may perform at most `k` increment operations on the array. In a single operation, you choose any element and increase its value by 1. Each operation increases exactly one element by 1, and no other changes are allowed.

Your task is to compute the maximum possible frequency (count of occurrences) of any single value in the array after performing at most `k` increment operations.

## Function Signature

```python
def solve(nums: list[int], k: int) -> int:
    ...
```

## Input

The solver is exposed through the Aura harness. The harness calls `solve(nums, k)` directly — there is **no stdin/stdout**. Instead, the test harness presents each case on the `CASE` lines:

```
CASE0= nums=[1,4,8,13], k=5
CASE1= nums=[3,9,6], k=2
CASE2= nums=[1,2,4], k=5
```

For each `CASEi` line, the harness parses the named arguments and invokes `solve(nums=..., k=...)`. Your function must return an `int`: the maximum achievable frequency of any element after at most `k` total increments.

## Output

A single integer per case — the largest possible frequency of any value in the array after applying at most `k` increment operations (operations may be distributed across any elements, but the total count of +1 increments across all elements cannot exceed `k`).

## Notes

- `1 <= len(nums) <= 10^5`, `1 <= nums[i] <= 10^9`, `0 <= k <= 10^14`.
- The operation only *increments* — you cannot decrement elements.
- A classic approach sorts the array and uses a sliding window, tracking the total increments needed to raise every element in the window up to the current (largest) window value. The window is valid when the required increments are within `k`; shrink from the left when not.
- Return `0` is not possible since `len(nums) >= 1` — the answer is at least `1` whenever `k >= 0` and the array is non-empty.
