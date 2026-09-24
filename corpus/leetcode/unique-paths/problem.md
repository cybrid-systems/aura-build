# Unique Paths

## Problem

You are given a grid with `m` rows and `n` columns. A robot starts at the top-left cell `(0, 0)` and wants to reach the bottom-right cell `(m-1, n-1)`. At each step, the robot may only move **right** or **down**. Count the number of unique paths from start to finish.

## Function Signature

```lisp
(solve m n) -> integer
```

- `m` — number of rows (positive integer)
- `n` — number of columns (positive integer)
- Returns the total number of unique paths.

## Input Convention

The harness invokes `(solve)` with no arguments. The case parameters are read from `*STDIN*` as `CASE0=...` style assignment lines, e.g.:

```
CASE0_M=3
CASE0_N=7
```

Your implementation should bind these values and call `(solve m n)` for each case.

## Output Convention

Print one line per case with the result, e.g.:

```
28
```

## Notes

- The answer fits in a standard 64-bit integer for typical constraints (`m, n <= 100`).
- This is a classic combinatorics / dynamic programming problem: the number of paths equals `C(m+n-2, m-1)`.
- Either a DP table or the combinatorial formula is acceptable.
