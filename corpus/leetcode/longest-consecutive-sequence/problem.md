# Longest Consecutive Sequence

## Problem

You are given an unsorted array of integers (which may contain duplicates). Find the length of the longest subsequence of consecutive integers. The subsequence need not occupy contiguous positions in the original array — only the values must be consecutive.

Formally, if the array is `a[0..n-1]`, determine the maximum `k` such that there exist indices `i_1 < i_2 < ... < i_k` with `a[i_2] = a[i_1] + 1`, `a[i_3] = a[i_2] + 1`, ..., `a[i_k] = a[i_{k-1}] + 1`.

### Example

```
Input:  [100, 4, 200, 1, 3, 2]
Output: 4
```
The longest consecutive sequence is `[1, 2, 3, 4]`.

```
Input:  [0, 3, 7, 2, 5, 8, 4, 6, 0, 1]
Output: 9
```
The whole range `0..8` is present.

## Function Signature

```
(defn solve [nums] ...)
```

- `nums`: a vector of integers (may include negatives and duplicates), length `n >= 0`.
- Returns: an integer, the length of the longest consecutive subsequence. If `nums` is empty, return `0`.

## I/O Convention (Aura harness)

The harness invokes `solve` directly on a single input. Inside the Aura runner, the case is configured via the `CASE0` block in the runner config:

```
CASE0 = nums = [100,4,200,1,3,2]
CASE0_EXPECT = 4
```

A single line of standard input is also accepted for ad-hoc testing: a JSON-array-style list, e.g. `[100,4,200,1,3,2]`.

## Constraints

- `0 <= n <= 10^6`
- Values fit in a signed 64-bit integer (`-2^63 .. 2^63 - 1`).
- Expected time complexity: **O(n)** average.
- Expected extra space: **O(n)**.

## Notes

- Duplicates must not be double-counted; treat each value as a set element.
- A naive sort gives O(n log n); the goal is a hash-set based O(n) solution.
- "Consecutive" refers to integer adjacency (`x, x+1, x+2, ...`), not positional adjacency.
