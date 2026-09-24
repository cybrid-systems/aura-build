# Kth Smallest Element in a Sorted Matrix

## Problem

You are given an `n x n` matrix where each row is sorted in ascending order (left to right) and each column is also sorted in ascending order (top to bottom). Given an integer `k`, return the **kth smallest element** among all elements in the matrix.

## Function Signature

```clojure
(defn solve [matrix k]
  ;; returns the k-th smallest element in the matrix
  )
```

## Input / Output Convention

Input is provided via standard input using the Aura `CASE0`/`CASE1`/... format.
- The first line contains the integer `n` (size of the matrix).
- The next `n` lines each contain `n` integers representing the matrix row.
- The final line contains the integer `k`.

**Example (CASE0):**

```
3
1 5 9
10 11 13
12 13 15
8
```

Expected output (CASE0):

```
13
```

## Notes

- All matrix elements are integers. `1 ≤ k ≤ n * n`.
- A row-/column-sorted matrix lets you efficiently pop the next smallest candidate using a min-heap seeded with the first column (or first row).
- Alternative approaches (e.g., binary search on value) are valid, but the heap approach mirrors the classic solution.
- Output only the resulting integer followed by a newline.
