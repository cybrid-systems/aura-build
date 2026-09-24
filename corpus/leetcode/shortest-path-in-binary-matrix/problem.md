# Shortest Path in Binary Matrix

## Problem

You are given an `n x n` binary grid. Each cell contains either `0` (clear) or `1` (blocked). Starting from the top-left cell `(0, 0)` and ending at the bottom-right cell `(n-1, n-1)`, find the length of the **shortest clear path**.

A clear path must satisfy:

- Every visited cell contains `0`.
- You may move in **8 directions**: horizontally, vertically, and diagonally (i.e., to any of the 8 neighboring cells).
- The path length is counted as the number of cells visited (the start and end cells included).
- The start and end cells must themselves be `0`; otherwise no valid path exists.

If no such path exists, return `-1`.

## Function Signature

```lisp
(defun solve (grid)
  ;; grid is a vector of vectors of integers (0 or 1), size n x n
  ;; returns the length of the shortest clear path, or -1 if none exists
  )
```

## Input

The input is provided on standard input, but in this harness the grid is passed directly to the `solve` function. For reference, the raw I/O convention used in the test cases is:

```
CASE0=((0 0 0) (1 1 0) (1 1 0))
CASE1=((0 1) (1 0))
CASE2=((1 0 0) (0 0 0) (0 0 1))
```

Where each case is an `n x n` grid of `0`s and `1`s.

## Output

Return a single integer: the length of the shortest clear path from `(0, 0)` to `(n-1, n-1)`, or `-1` if no path exists.

## Examples

| Grid | Expected Output | Reason |
|------|----------------|--------|
| `((0 0 0) (1 1 0) (1 1 0))` | `4` | Path: `(0,0) -> (0,1) -> (0,2) -> (1,2) -> (2,2)` |
| `((0 1) (1 0))` | `-1` | Start and end are clear but no 8-connected path exists |
| `((1 0 0) (0 0 0) (0 0 1))` | `6` | Must use diagonals to bypass the corners |

## Notes

- Use **BFS** from `(0, 0)` to guarantee the shortest path; DFS would explore unnecessarily many paths.
- Movement is **8-directional**, so remember to update all 8 neighbors `(dx, dy)` in `{-1, 0, 1} x {-1, 0, 1}` excluding `(0, 0)`.
- If the grid is `1 x 1` and contains only `0`, the answer is `1` (a single cell path).
- Track visited cells to avoid cycles; mark a cell visited upon enqueueing it.
