# Search a 2D Matrix II

## Problem

You are given an `m x n` integer matrix with the following two properties:

- Each row is sorted in non-decreasing order.
- Each column is sorted in non-decreasing order.

Given an integer `target`, return `true` if `target` is in the matrix, otherwise return `false`.

You must write an algorithm with a time complexity better than O(m · n). A staircase (or "search from corner") approach using O(m + n) comparisons is the intended solution.

## Function Signature

```clojure
(solve MATRIX TARGET)
```

- `MATRIX` — a vector of vectors of integers, e.g. `[[1 4 7 11 15] [2 5 8 12 19] [3 6 9 16 22] [10 13 14 17 24] [18 21 23 26 30]]`.
- `TARGET` — an integer.

Return `true` if `TARGET` exists in `MATRIX`, otherwise `false`.

## Input / Output Convention

Each test case is provided as two consecutive `CASE0=...` lines on stdin:

```
CASE0=<matrix in Clojure literal form, e.g. [[1 4 7 11 15] [2 5 8 12 19] [3 6 9 16 22] [10 13 14 17 24] [18 21 23 26 30]]>
CASE0=<target integer, e.g. 5>
```

Your function should print either `true` or `false` (lowercase) as the answer for that case.

## Notes

- The matrix is guaranteed to satisfy both row-sorted and column-sorted invariants.
- Empty rows are not expected; if `MATRIX` is empty (no rows) or any row is empty, the answer is `false`.
- Staircase search: start at the top-right corner; move **left** when the current value is greater than `TARGET`, **down** when it is smaller, and stop when you either find `TARGET` or move out of bounds.
- Do **not** use a nested scan of all `m · n` cells; the intended complexity is O(m + n).
