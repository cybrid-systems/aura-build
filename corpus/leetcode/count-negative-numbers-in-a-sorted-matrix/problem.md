# Count Negative Numbers in a Sorted Matrix

## Problem

You are given an `m x n` matrix `grid` where each row and each column is sorted in **non-increasing** order (i.e., values decrease or stay the same when moving right within a row or down within a column).

Return the total number of **negative** numbers in the matrix.

The matrix dimensions and the value distribution make a full scan wasteful — exploit the sorted structure to achieve better than `O(m*n)` time.

## Function Signature

```lisp
(defun solve (grid)
  ;; returns the count of negative numbers
  )
```

## Input

A single test case is read from standard input.

- Line 1: two integers `m` and `n` (matrix dimensions).
- Lines 2..m+1: each line contains `n` integers representing one row of the matrix.

### I/O Convention (CASE0)

```
CASE0=grid
5 4
 4  3  2 -1
 3  2  1 -1
 1  1 -1 -2
-1 -1 -2 -3
-2 -3 -3 -4
```

The harness feeds the parsed `grid` to `solve` and prints the returned integer.

## Output

A single integer: the number of negative entries in `grid`.

## Notes

- Each row and column is sorted **non-increasingly**, so once a non-negative value is found, every value to its left (within the same row) is non-negative too, and every value below it is also non-negative.
- A typical efficient approach starts from the top-right (or bottom-left) corner and walks in `O(m + n)` steps, or performs a binary search per row for `O(m log n)`.
- Duplicates and zeros are allowed; only strictly negative values (`< 0`) should be counted.
