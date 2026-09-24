# 3Sum

## Problem

Given an integer array `nums`, return **all unique triplets** `[nums[i], nums[j], nums[k]]` such that:

- `i`, `j`, and `k` are distinct indices,
- `nums[i] + nums[j] + nums[k] == 0`.

The solution set must not contain duplicate triplets (the values within each triplet may be in any order, but the triplets themselves must be unique).

### Examples

**Example 1**
```
Input:  nums = [-1, 0, 1, 2, -1, -4]
Output: [[-1, -1, 2], [-1, 0, 1]]
```

**Example 2**
```
Input:  nums = [0, 1, 1]
Output: []
```

**Example 3**
```
Input:  nums = [0, 0, 0]
Output: [[0, 0, 0]]
```

## Function Signature

```clojure
(defn solve [nums] ...)
```

- `nums` — a vector of integers (may contain negatives, zeros, and duplicates; length `0 ≤ n ≤ 3000`).
- Returns a vector of triplets (each a vector of three integers) containing every unique triplet summing to zero, in any order. Triplets themselves need not be sorted, but duplicate triplets are not allowed.

## Input / Output Convention (Aura harness)

- A single line: `CASE0=-1,0,1,2,-1,-4`
- `CASE0=` is the marker; the comma-separated tokens after it form the input vector `nums`.
- Output: the resulting triplets, one per line, each formatted as comma-separated values inside square brackets, e.g.
  ```
  [-1,-1,2]
  [-1,0,1]
  ```
- If no triplet exists, print a single line: `[]`

## Notes

- The same triplet of values must never appear twice in the output (e.g., `[-1,0,1]` and `[-1,0,1]` are duplicates even if derived from different indices).
- An efficient approach sorts the array first (`O(n log n)`) and then uses a two-pointer scan per anchor element, skipping over duplicate values to avoid repeated triplets, giving an overall `O(n²)` time complexity.
- Be careful with edge cases: empty input, all-zero input, and inputs with many duplicates that could otherwise produce repeated triplets.
