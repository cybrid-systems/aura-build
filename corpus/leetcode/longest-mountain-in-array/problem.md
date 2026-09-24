# Longest Mountain in Array

## Problem Statement

Given an integer array `arr`, return the length of the longest "mountain" in the array.

A **mountain** is defined as a subarray that:
- Has **at least 3 elements**.
- Strictly **increases** by at least one element.
- Strictly **decreases** by at least one element.
- Reaches a **peak** (single highest element) from which it descends.

If there is no mountain, return `0`.

### Examples

```
Input:  arr = [2, 1, 4, 7, 3, 2, 5]
Output: 5
Explanation: The longest mountain is [1, 4, 7, 3, 2] with length 5.

Input:  arr = [2, 2, 2]
Output: 0
Explanation: No strict increase/decrease exists, so no mountain.

Input:  arr = [1, 3, 1, 4, 5, 6, 7, 8, 9, 8, 7, 6, 5, 4, 3, 2, 0]
Output: 15
Explanation: A single long mountain runs almost the full array.
```

## Function Signature

```clojure
(solve arr)
```

- `arr` — a vector of integers (non-empty).
- Returns the length of the longest mountain as an integer.

## Input Convention (Harness)

The harness reads a single line per test case, whitespace-separated integers:

```
CASE0=2 1 4 7 3 2 5
CASE1=2 2 2
CASE2=1 3 1 4 5 6 7 8 9 8 7 6 5 4 3 2 0
```

For each `CASEn=...` line, parse the integers after `=` as `arr`, invoke `(solve arr)`, and collect the result. There is no stdin in the Aura harness — the `solve` function is called directly with parsed arguments.

## Notes

- Edge cases to watch: flat plateaus at any point (no strict rise/fall) break a mountain; arrays shorter than 3 elements can never form a mountain and should return `0`.
- A single peak traversed with two pointers (one ascending from the left base, one descending from the right base) is sufficient — no nested scans are required.
- Expected complexity: **O(n)** time, **O(1)** extra space.
