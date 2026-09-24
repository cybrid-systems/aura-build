# House Robber II

You are a professional robber planning to rob houses arranged in a circle. Each house has a non-negative amount of money, and you cannot rob two adjacent houses (because that would alert the police). Since the houses are in a circle, the first and last houses are also adjacent.

Given an array `nums` where `nums[i]` is the amount of money in the *i*-th house, return the maximum amount of money you can rob in one night without alerting the police.

## Function Signature

```
(solve [nums]) -> integer
```

## Input / Output Format

Input is provided as a single line via standard input in the following form:

```
CASE0=nums=[2,3,2]
```

- The value after `nums=` is the list of house values, written as a JSON-style array.
- There is exactly one test case per line.

Output the maximum loot as a single integer on its own line.

## Notes

- `nums` is guaranteed to contain at least one element.
- A house at index `i` (where `0 ≤ i < n-1`) is considered adjacent to its neighbors at indices `i-1` and `i+1`. Additionally, the house at index `0` is adjacent to the house at index `n-1`.
- A convenient reduction is to consider two linear versions of the problem: one that excludes the first house, and another that excludes the last house, then take the maximum of the two results.
- Each individual `nums[i]` is a non-negative integer.
