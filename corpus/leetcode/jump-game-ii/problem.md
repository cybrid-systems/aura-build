# Jump Game II

## Problem

You are given an array `nums` of length `n` where each `nums[i]` represents the maximum jump length you can take from index `i`. Starting at index `0`, return the **minimum number of jumps** required to reach the last index (`n - 1`). It is guaranteed that the last index is reachable.

## Function Signature

```python
def solve(nums: list[int]) -> int:
    ...
```

## Input / Output

The harness feeds input on **stdin** in the following form:

```
CASE0=n
<length-n line>
CASE1=<len1>
<...>
```

For each case, the array `nums` is read as space-separated integers from a single line, and your `solve` function must return the minimum number of jumps to reach the last index.

## Notes

- `2 <= len(nums) <= 10^5`, `0 <= nums[i] <= 1000`.
- The last index is always reachable, so the answer is well-defined.
- Aim for **O(n)** time and **O(1)** extra space — a single greedy sweep over the array is enough.
