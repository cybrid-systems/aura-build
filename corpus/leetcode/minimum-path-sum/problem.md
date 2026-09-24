# Minimum Path Sum

## Problem

You are given an `m × n` grid of non-negative integers. Starting from the cell at the top-left corner `(0, 0)` and ending at the cell at the bottom-right corner `(m - 1, n - 1)`, find a path whose sum of visited cell values is minimized. From any cell you may only move **right** or **down**.

Return the minimum possible sum of a valid path.

## Function Signature

```python
def solve(grid: list[list[int]]) -> int:
    ...
```

## Input

The input is provided on stdin in a simple line-based format:

```
M N
a00 a01 ... a0(N-1)
a10 a11 ... a1(N-1)
...
a(M-1)0 ... a(M-1)(N-1)
```

- `M`, `N` — the grid dimensions (`1 <= m, n <= 200`).
- The following `M` lines each contain `N` space-separated integers (`0 <= a_ij <= 100`).

## Output

Print a single integer: the minimum path sum from `(0, 0)` to `(m - 1, n - 1)`.

## Examples

### Example 1

Input:
```
3 3
1 3 1
1 5 1
4 2 1
```

Output:
```
7
```
Explanation: The optimal path `1 → 3 → 1 → 1 → 1` has sum `7`. (Equivalently `1 → 1 → 4 → 2 → 1` also sums to `9`, not optimal; the minimum is `7`.)

### Example 2

Input:
```
2 2
1 2
3 4
```

Output:
```
7
```

## Notes

- The grid is guaranteed to contain at least one cell, so `M, N >= 1`.
- Standard 2D dynamic programming works in `O(m · n)` time with `O(n)` extra memory (rolling row) or `O(1)` if you mutate `grid` in place.
- Overflow is not a concern: with `m, n <= 200` and values up to `100`, the maximum possible sum is well within 32-bit integer range.
