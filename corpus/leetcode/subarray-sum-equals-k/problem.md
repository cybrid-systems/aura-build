# Subarray Sum Equals K

## Problem Statement

You are given an array of integers `nums` and an integer `k`. Return the total number of **continuous** subarrays whose elements sum to exactly `k`.

A continuous subarray is any non-empty slice `nums[i..j]` where `0 ≤ i ≤ j < nums.length`.

### Examples

**Example 1**
```
Input:  nums = [1, 1, 1], k = 2
Output: 2
Explanation: The subarrays [1,1] at indices (0,1) and (1,2) both sum to 2.
```

**Example 2**
```
Input:  nums = [1, 2, 3], k = 3
Output: 2
Explanation: The subarrays [1,2] (indices 0..1) and [3] (index 2) sum to 3.
```

**Example 3**
```
Input:  nums = [1, -1, 1, -1, 1, -1], k = 0
Output: 6
Explanation: Multiple subarrays sum to 0; count them all.
```

## Function Signature

```clojure
(defn solve [nums k] ...)
```

- `nums` — a vector of integers (may contain negative values and zeros).
- `k` — an integer target sum.
- Returns an integer: the count of continuous subarrays whose sum equals `k`.

## Input / Output Convention

The harness reads a single case from a `CASE0` constant in the source file. Use the format:

```
CASE0=INPUT
nums=1,1,1
k=2
CASE0=OUTPUT
2
```

The first `CASE0=INPUT` block contains the parameters; the `CASE0=OUTPUT` block contains the expected answer used for verification.

## Notes

- `nums.length` is up to ~10⁵, so an O(n) solution using a prefix-sum hash map is expected.
- Subarrays may contain negative numbers, so a sliding-window approach does **not** apply — prefer the prefix-sum + hashmap method.
- The answer fits in a standard 64-bit signed integer.
