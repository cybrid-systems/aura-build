# Unique Paths II

## Problem

You are given an `m x n` grid where each cell is either empty (`0`) or contains an obstacle (`1`).

Starting from the top-left cell `(0, 0)`, you want to reach the bottom-right cell `(m-1, n-1)`. At each step you may move only **right** or **down** into an adjacent cell. You cannot step onto a cell containing an obstacle, and you also cannot start or end on an obstacle.

Count the number of **unique** paths from start to finish. Since the answer can be very large, return it modulo `1_000_000_007`.

If no valid path exists, return `0`.

## Input

The first line contains a single integer `T` — the number of test cases.

For each test case:
- The first line contains two integers `m` and `n` (the grid dimensions).
- The next `m` lines each contain `n` space-separated integers (`0` or `1`) representing the grid.

## Output

For each test case, output a single line containing the answer modulo `1_000_000_007`.

## Function Signature

```haskell
solve :: [[Int]] -> Int
```

- Input: a list of test cases, where each test case is the grid (a list of rows, each row a list of `Int`s with `0` for empty and `1` for obstacle).
- Output: a list of answers, one per test case (modulo `1_000_000_007`).

## Notes

- `m` and `n` can each be up to `100`, so `dp[i][j] = dp[i-1][j] + dp[i][j-1]` (skipping obstacles) is efficient enough.
- Edge cases: a single-cell grid that is an obstacle (`[[1]]`) should return `0`; a single empty cell (`[[0]]`) should return `1`.
- Use `1_000_000_007` (i.e. `1000000007`) as the modulus everywhere; remember to apply it after every addition to avoid overflow.
