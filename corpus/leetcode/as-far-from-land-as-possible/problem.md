# As Far from Land as Possible

## Problem

You are given an `n x n` grid `grid` where each cell is either land (`1`) or water (`0`). A cell is on the boundary of the grid if `i == 0`, `i == n - 1`, `j == 0`, or `j == n - 1`.

Your task is to find a water cell that is as far as possible from any land cell. More precisely, for every water cell, compute the minimum Manhattan-style (grid) distance to any land cell. Return the **maximum** of these distances. If the grid contains only land or only water, return `-1`.

Movement between cells is allowed in the four cardinal directions (up, down, left, right), and distance is measured as the number of steps between adjacent cells.

## Function Signature

```
(defn solve [grid]
  ;; returns Long
  )
```

- `grid`: a vector of vectors of integers (`0` or `1`), representing an `n x n` matrix (`1 <= n <= 100`).

## Input / Output Convention

The harness drives the function directly with a Clojure value; no stdin/stdout is used. Example case constants used by the test harness:

```
CASE0=grid [[1,0,1],[0,0,0],[1,0,1]]                -> expected 2
CASE1=grid [[1,0,0],[0,0,0],[0,0,0]]                -> expected 4
CASE2=grid [[1,1,1],[1,1,1],[1,1,1]]                -> expected -1
CASE3=grid [[0,0,0],[0,0,0],[0,0,0]]                -> expected -1
```

## Notes

- A single multi-source BFS starting from all land cells simultaneously gives each water cell its minimum distance to the nearest land in `O(n^2)` time.
- Watch out for the two degenerate cases: all-land (no water) and all-water (no land) — both should return `-1`.
- Cells at the boundary can still be valid answers (e.g., `CASE1` selects a corner water cell).
