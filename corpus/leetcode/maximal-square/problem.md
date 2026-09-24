# Maximal Square

## Problem

You are given a 2D binary matrix (`0`/`1`) of size `m × n`. Find the side length of the **largest square** that contains **only `1`s**, and return its **area**.

If the matrix contains no `1`s, return `0`.

## Function Signature

```text
(solve m n grid) -> int
```

- `m`, `n` — integers, the number of rows and columns (`1 ≤ m, n ≤ 100`).
- `grid` — a list of `m` lists, each containing `n` integers (`0` or `1`).
- Returns the **area** of the largest all-`1` square.

## Input / Output Convention

Input arrives **before** the call as `CASE0=...` lines on stdin. Each line is a key/value pair:

```text
CASE0_M=4
CASE0_N=5
CASE0_GRID=[[1,0,1,0,0],[1,0,1,1,1],[1,1,1,1,1],[1,0,0,1,0]]
```

Your `(solve m n grid)` is then called with those values, and its return value is printed as the answer.

## Example

**Input**

```text
CASE0_M=4
CASE0_N=5
CASE0_GRID=[[1,0,1,0,0],[1,0,1,1,1],[1,1,1,1,1],[1,0,0,1,0]]
```

**Output**

```text
4
```

(The largest all-`1` square has side length `2`, so its area is `4`.)

## Notes

- Standard DP recurrence: `dp[i][j] = min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1]) + 1` when `grid[i][j] == 1`.
- The answer to return is the **square of** the maximum side length found, not the side length itself.
- Time complexity `O(m·n)` and `O(n)` extra space are both achievable.
