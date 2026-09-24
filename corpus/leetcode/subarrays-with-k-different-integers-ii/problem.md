# Subarrays With At Most K Different Integers

## Problem

Given an integer array `nums` and an integer `k`, count the number of contiguous subarrays of `nums` that contain **at most** `k` distinct integers.

A subarray is a contiguous non-empty sequence of elements from the array.

## Function Signature

```haskell
solve :: [Int] -> Int -> Int
```

The first argument is the input array `nums`, and the second argument is `k`. Return the count of subarrays with at most `k` distinct integers.

## Input Convention

The input is provided on a single line via standard input as two space-separated values:

- The first value is `k`.
- The remaining values form the array `nums`.

**Example:**

```
CASE0=k=3 nums=1 2 1 2 3
```

For this example:

- `k = 3`
- `nums = [1, 2, 1, 2, 3]`
- Expected output: `7` (the subarrays are: `[1]`, `[2]`, `[1]`, `[2]`, `[3]`, `[1,2]`, `[2,1]`, `[1,2]`, `[2,3]`, `[1,2,1]`, `[2,1,2]`, `[1,2,1,2]`, `[2,1,2,3]`, `[1,2,1,2,3]`; those with at most 3 distinct integers total 7)

The function will be tested against multiple cases. Each case is given as one line in the format shown above.

## Output Convention

Print a single integer per case: the count of subarrays with at most `k` distinct integers.

## Notes

- Use the sliding window technique: maintain a window `[left, right]` with a frequency map, and expand `right` while shrinking `left` when distinct count exceeds `k`.
- The count of valid subarrays ending at each `right` is simply `right - left + 1`.
- Edge case: when `k = 0`, the answer is `0` (no subarray has 0 distinct integers since subarrays are non-empty).
- Constraints to keep in mind: the array can be large (up to ~10^5 elements), so an O(n) approach is required.
