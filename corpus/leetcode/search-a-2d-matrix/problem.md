# Search a 2D Matrix

## Problem

You are given an `m x n` integer matrix with the following two properties:

- Each row is sorted in strictly increasing order.
- The first integer of each row is greater than the last integer of the previous row.

Write a program that searches for a `target` value in this matrix. Return `true` if the target exists in the matrix, otherwise return `false`.

Your solution must run in **O(log(m * n))** time.

## Function Signature

```
def solve(target: int, matrix: list[list[int]]) -> bool
```

The `solve` function receives the target value and the matrix (as a list of lists of ints) and must return a boolean indicating whether the target is found.

## Input / Output Convention

Input arrives on standard input as a single test case formatted as `CASE0=...` lines:

```
CASE0=target=<int>
CASE0=row0=[<int>,<int>,...,<int>]
CASE0=row1=[<int>,<int>,...,<int>]
...
CASE0=matrix=<rows>x<cols>
```

Each `CASE0=row<i>` line contains the integers of row `i`, separated by commas and wrapped in `[ ]`. The `CASE0=matrix=<rows>x<cols>` line declares the matrix dimensions. The matrix is guaranteed to satisfy the sorted-row / first-of-row-greater-than-last-of-previous-row properties. Output the single line:

```
True
```

or

```
False
```

## Notes

- You may treat the matrix as a single virtual sorted array of length `m * n` and binary-search on it: index `i` maps to `matrix[i // n][i % n]`.
- An alternative is a two-stage binary search (locate the row, then the column), but the flat-index approach is simpler.
- Edge cases include empty rows, a 1-row matrix, and a 1-column matrix — your implementation must handle all of them correctly.
- Assume the input is well-formed; no need to validate `CASE0=` syntax beyond reading the values.
