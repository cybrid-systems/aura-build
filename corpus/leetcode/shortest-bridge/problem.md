# Shortest Bridge

## Problem

You are given an `n x n` binary matrix `grid` containing only `0`s and `1`s. The `1`s represent land and the `0`s represent water.

It is guaranteed that there are exactly **two** islands in the grid (connected components of `1`s, connected 4-directionally). You may flip any number of `0`s to `1`s (i.e., build a bridge by converting water cells to land) to connect the two islands.

Return the **minimum number of `0`s that must be flipped** so that the two islands become connected (4-directionally).

## Function Signature

```python
def solve(grid: list[list[int]]) -> int:
    ...
```

## Input

Input is provided on standard input as a single test case.

- Line 1: integer `n` — the size of the grid.
- Lines 2..n+1: `n` space-separated integers (`0` or `1`) representing one row of `grid`.

### Convention (CASE0)

```
CASE0=
4
0 1 0 0
0 0 0 0
0 0 1 0
0 0 0 0
```

The harness strips the `CASE0=` marker and the leading/trailing blank lines, and feeds the remaining lines to `solve`.

## Output

Print a single integer — the minimum number of water cells that must be flipped to connect the two islands.

For the example above the answer is `3`.

## Notes

- `1 <= n <= 100`. There are exactly two islands.
- A standard approach: locate one island (DFS/BFS to collect its cells), then multi-source BFS from all of its cells simultaneously, counting expansion steps until any BFS layer reaches the other island. The number of layers expanded through water cells equals the minimum flips required.
- Edge cases: adjacent islands already touching (`0` flips) must still be handled correctly by your BFS termination condition.
