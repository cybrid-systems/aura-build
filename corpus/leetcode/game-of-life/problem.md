# Game of Life

## Problem

You are given a rectangular grid representing one generation of Conway's Game of Life. Compute the **next** generation **in place**, following the standard rules:

- A live cell (1) with fewer than 2 live neighbors **dies** (underpopulation).
- A live cell with 2 or 3 live neighbors **survives**.
- A live cell with more than 3 live neighbors **dies** (overpopulation).
- A dead cell (0) with **exactly** 3 live neighbors **becomes alive** (reproduction).

Neighbors are the 8 cells sharing an edge or corner. The grid is **finite**; cells outside the bounds have no neighbors.

Because the update must be **in place**, encode the new state using only the grid cells:

- A cell that goes from `1` → `0` is marked `2`.
- A cell that goes from `0` → `1` is marked `3`.

The caller will translate `2 → 0` and `3 → 1` after `solve` returns.

## Function Signature

```lisp
(defun solve (grid)
  "Update GRID in place from generation N to generation N+1 of Game of Life.
   Use marker 2 for dying live cells and marker 3 for newly born cells."
  ...)
```

## Input

Read from `*standard-input*` using the harness's `CASE0` / `CASE1` / … format:

```
CASE0
R C
r0c0 r0c1 ... r0c{C-1}
r1c0 r1c1 ... r1c{C-1}
...
r{R-1}c0 ... r{R-1}c{C-1}
CASE1
...
```

Each cell value is `0` or `1`. `R, C ≥ 1`.

## Output

For each case, print `R` lines of `C` integers separated by single spaces, showing the grid after `solve` has applied the in-place update (i.e. still containing the `2`/`3` markers).

```
m0,0 m0,1 ... m0,C-1
m1,0 m1,1 ... m1,C-1
...
```

## Notes

- Use the `2`/`3` marker trick so a single pass can decide each cell's next state from a snapshot of the current generation.
- Edge and corner cells simply count fewer neighbors; no wrapping is applied.
- Complexity should be `O(R·C)` time and `O(1)` extra space (the marker values already fit in a cell).
