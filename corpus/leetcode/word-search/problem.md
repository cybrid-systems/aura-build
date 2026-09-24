# Word Search

## Problem

Given an `m x n` grid of characters `board` and a string `word`, determine if `word` can be formed by connecting cells **horizontally or vertically** (4-directional adjacency) in the grid. Each cell may be used **at most once** per path.

Return `true` if the word exists, otherwise `false`.

## Input

- Line 1: two integers `m n` — board dimensions
- Lines 2..m+1: `n` characters each (use `.` to represent empty cells; treat them as non-matching)
- Line m+2: the target string `word`

## Output

Print `YES` if the word can be traced in the board, else `NO`.

## Function Signature

```lisp
(defun solve (m n board word)
  ;; return T or NIL
  )
```

## I/O Convention (Aura harness)

```
CASE0=NO
CASE1=YES
```

The harness will call `(solve ...)` and compare the return value against each `CASEi=...` line.

## Notes

- Use DFS with backtracking: mark a cell as visited when entering, restore it when leaving.
- Start the DFS from every cell matching the first character of `word`.
- The empty string trivially matches; if `word` is empty, return `T`.
- `m, n ≤ 6` in the test cases, so brute-force backtracking is sufficient.
