# Spiral Matrix

## Problem

Given an `m x n` matrix of integers, return all elements of the matrix in **spiral order** — that is, starting from the top-left corner, traverse right across the top row, then down the rightmost column, then left across the bottom row, then up the leftmost column, and continue inward until every element has been visited.

## Function Signature

```lisp
(defun solve (matrix)
  ;; returns a list of integers in spiral order
  )
```

## Input

Read a single test case from standard input in the following format:

```
CASE0=<m>
<n>
<a11> <a12> ... <a1n>
<a21> <a22> ... <a2n>
...
<am1> <am2> ... <amn>
```

- `m` — number of rows (1 ≤ m ≤ 100)
- `n` — number of columns (1 ≤ n ≤ 100)
- Each `aij` is an integer in the range [-1000, 1000]

## Output

Print the elements in spiral order on a single line, separated by single spaces, followed by a newline.

## Examples

### Example 1

**Input**
```
CASE0=3
3
1 2 3
4 5 6
7 8 9
```

**Output**
```
1 2 3 6 9 8 7 4 5
```

### Example 2

**Input**
```
CASE0=3
4
1 2 3 4
5 6 7 8
9 10 11 12
```

**Output**
```
1 2 3 4 8 12 11 10 9 5 6 7
```

## Notes

- The `CASE0=` line is the harness-specific case marker; the value after `=` (`m`) is also given on the next line for convenience — both refer to the number of rows.
- A single-row or single-column matrix is a valid edge case: the traversal degenerates to a straight line.
- An `m x n` matrix has `m * n` elements; the output must contain exactly that many numbers.
