# Kth Smallest Element in a Sorted Matrix

## Problem Statement

Given an `n x n` matrix where each of the rows and columns is sorted in strictly increasing order, return the **k-th smallest element** in the matrix.

Note that it is the k-th smallest element in the sorted order, not the k-th distinct element.

You must find an algorithm with runtime complexity better than `O(n² log n)` (i.e., something sub-quadratic).

## Function Signature

```clojure
(solve n matrix k)
```

- `n` — integer, the size of the matrix (matrix is `n x n`)
- `matrix` — a vector of `n` vectors, each of length `n`, with `matrix[i][j]` sorted left-to-right and top-to-bottom in strictly increasing order
- `k` — integer, 1-indexed rank to retrieve (`1 ≤ k ≤ n*n`)
- Returns the k-th smallest element in the matrix.

## Input / Output Convention

Your solution is invoked by a harness that reads from an embedded registry (no stdin). Each test case is registered under a key like `CASE0`, `CASE1`, …, and the harness calls `(solve ...)` with the decoded arguments.

Example entries the harness might expose:

```
CASE0 = {:n 3 :matrix [[1 5 9] [10 11 13] [12 13 15]] :k 8}
CASE1 = {:n 2 :matrix [[1 2] [3 4]]                     :k 3}
```

Expected returns:

```
CASE0 -> 13   ; sorted: [1,5,9,10,11,12,13,13,15], 8th = 13
CASE1 -> 3    ; sorted: [1,2,3,4], 3rd = 3
```

## Notes

- Values fit comfortably in standard 32-bit integers, but treat the comparison generically.
- A binary-search-on-value approach runs in `O(n log(max-min))` by counting, for each candidate `mid`, how many matrix entries are `≤ mid` using the row/column sortedness (start from bottom-left or top-right and walk in one direction).
- Tie-breaking: since rows and columns are *strictly* increasing within each, equals do not occur on the same row or column — but duplicates across different rows/columns are allowed, so "k-th smallest" counts multiplicities.
- Edge cases: `k = 1` (return the top-left `matrix[0][0]`), `k = n*n` (return the bottom-right `matrix[n-1][n-1]`).
