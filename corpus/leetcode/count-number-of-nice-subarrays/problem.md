# Count Number of Nice Subarrays

## Problem Statement

You are given an array of integers `nums` and an integer `k`. A subarray is called **nice** if it contains **exactly `k` odd numbers**.

Return the number of nice subarrays.

## Function Signature

```python
def solve(nums: list[int], k: int) -> int:
    ...
```

## Input / Output Convention

The solution is invoked by the Aura harness directly (no stdin). Each test case is presented to your `solve` function as two positional/keyword arguments:

```
CASE0 = (nums=[...], k=...)           # expects int return
CASE1 = (nums=[...], k=...)
...
```

Your function must return the **count** of subarrays of `nums` that contain exactly `k` odd numbers.

## Example

```
nums = [1, 1, 2, 1, 2], k = 3
-> 2
```

The nice subarrays are `[1,1,2,1]` and `[1,2,1]` (each contains exactly 3 odd numbers).

## Notes

- `1 <= len(nums) <= 10^5` and `1 <= k <= len(nums)`.
- Elements satisfy `1 <= nums[i] <= 10^5`.
- Use the **sliding window** technique: the number of subarrays with exactly `k` odds equals `(count with at most k odds) - (count with at most k-1 odds)`. Aim for O(n) time and O(1) extra space.
- An element is odd if `nums[i] % 2 == 1`.
