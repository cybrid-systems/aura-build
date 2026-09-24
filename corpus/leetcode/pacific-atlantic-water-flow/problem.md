# Pacific Atlantic Water Flow

## Problem Statement

You are given an `m x n` integer matrix `heights` representing the heights of a rectangular grid of land. Water can flow from any cell to its neighboring cells in the four cardinal directions (up, down, left, right), but only when the destination cell has a height **less than or equal to** the source cell's height.

The **Pacific Ocean** touches the grid's left and top edges, and the **Atlantic Ocean** touches the grid's right and bottom edges.

Return a list of all grid coordinates `[row, col]` from which water can flow to **both** the Pacific and Atlantic oceans. Coordinates may be returned in any order.

## Function Signature

```clojure
(solve heights)
```

- `heights`: a vector of vectors of integers (e.g., `[[1 2 2 3 5] [3 2 3 4 4] [2 4 5 3 1] [6 7 1 4 5] [5 1 1 2 4]]`).
- Returns a vector of `[row col]` pairs (as vectors of two integers) representing cells that can reach both oceans.

## I/O Convention

The harness will print the input grid and the expected cells in `CASE0=...` form. For example:

```
CASE0=heights=[[1,2,2,3,5],[3,2,3,4,4],[2,4,5,3,1],[6,7,1,4,5],[5,1,1,2,4]]
CASE0=out=[[0,4],[1,3],[1,4],[2,2],[3,0],[3,1],[4,0]]
```

Your implementation should:

1. Read the `CASE0=heights=...` line and parse the matrix.
2. Read the `CASE0=out=...` line (or a separate expected-output line) and compare it against your computed set of cells (order-insensitive).

## Notes

- The standard approach performs two BFS/DFS traversals — one starting from all cells touching the Pacific (top row + left column) and one from all cells touching the Atlantic (bottom row + right column), walking **inward** along non-decreasing heights. The answer is the intersection of the two reachable sets.
- Coordinate format is zero-indexed: `(row, col)` with `0 <= row < m` and `0 <= col < n`.
- A cell on a shared border (e.g., top-left corner) borders both oceans automatically.
- Output ordering does not matter; compare as sets of `[row col]` pairs.
