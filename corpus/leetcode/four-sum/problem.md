# 4Sum

## Problem

Given an integer array `nums` and an integer `target`, return all unique quadruplets `[nums[a], nums[b], nums[c], nums[d]]` such that:

- `a`, `b`, `c`, `d` are distinct indices
- `nums[a] + nums[b] + nums[c] + nums[d] == target`

The quadruplets themselves must be unique (no duplicates), but the indices are not required to be in any particular order. The order of the returned list and the order within each quadruplet does not matter.

### Example

```
Input:  nums = [1,0,-1,0,-2,2], target = 0
Output: [[-2,-1,1,2],[-2,0,0,0],[-1,0,0,1]]

Input:  nums = [2,2,2,2,2], target = 8
Output: [[2,2,2,2]]
```

## Function Signature

Write a function `solve(nums, target)` that returns the list of unique quadruplets.

```python
def solve(nums: list[int], target: int) -> list[list[int]]:
    ...
```

## Input / Output Convention (CASE format)

Each case line contains a literal assignment. Parse the right-hand side as a Python expression.

- For arrays, use a list literal such as `[1,0,-1,0,-2,2]`.
- For the target, use an integer literal such as `0`.

Read pairs until EOF:

```
CASE0 = solve(nums=[1,0,-1,0,-2,2], target=0)
CASE1 = solve(nums=[2,2,2,2,2], target=8)
...
```

For each case, run `solve(nums=<array>, target=<int>)` and compare the returned list against the expected list of quadruplets (order-insensitive within and across quadruplets).

## Notes

- The output is a list of lists of integers. Each inner list is a quadruplet.
- Quartets whose elements are the same but appear in different index orderings are considered the same quadruplet.
- An empty result is represented as `[]`.
- The input array may contain duplicates, negative numbers, and zero; its length `n` satisfies `0 <= n <= 200`.
- Aim for an `O(n^3)` solution in practice by sorting and using a three-pointer / two-pointer sweep.
