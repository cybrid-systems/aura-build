# Shortest Subarray with Sum at Least K

## Problem

You are given an integer array `nums` (which may contain both positive and negative integers) and an integer `K`.

Return the length of the shortest non-empty subarray of `nums` whose sum is **at least** `K`. If no such subarray exists, return `-1`.

A subarray is a contiguous non-empty sequence of elements within the array.

## Function Signature

```haskell
solve :: [Int] -> Int -> Int
```

- The first argument is the list `nums`.
- The second argument is `K`.
- Return the length of the shortest subarray with sum ≥ `K`, or `-1` if none exists.

## Input / Output Convention

Input is provided on standard input as two **CASE** lines (no extra prompts, no examples in the actual stream):

```
CASE0=<comma-separated integers>
CASE1=<K>
```

Where `<comma-separated integers>` lists the elements of `nums` in order (e.g. `2,-1,3,-2,4`), and `<K>` is the target sum as a single integer.

Output: a single integer written to standard output — the answer to the single test case.

## Examples

For `nums = [2, -1, 3, -2, 4]` and `K = 5`, the answer is `3` (subarray `[3, -2, 4]` has sum `5`).

For `nums = [-1, 2]` and `K = 3`, no subarray reaches sum `3`, so the answer is `-1`.

## Notes

- `nums` is **not** guaranteed to be non-negative, so a plain two-pointer sliding window over the array does **not** work. An O(n) prefix-sum + monotonic deque approach is the intended technique.
- The answer is `-1` when no subarray has sum ≥ `K`.
- An empty subarray does not count; only non-empty subarrays are considered.
