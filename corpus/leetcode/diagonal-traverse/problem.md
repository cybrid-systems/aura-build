# Diagonal Traverse

## Problem

Given an `m x n` matrix, return all elements in **diagonal order**. Diagonal order visits elements that share the same `(row + col)` sum, starting from the smallest sum up to `m + n - 2`. Within each diagonal, the direction alternates: even-indexed diagonals (sum is even) are traversed from bottom to top, and odd-indexed diagonals from top to bottom.

### Example 1

```
Input:
3 3
1 2 3
4 5 6
7 8 9

Output:
1 2 4 7 5 3 6 8 9
```

Explanation:
- Diagonal sum 0: `[1]` → up
- Diagonal sum 1: `[2, 4]` → down
- Diagonal sum 2: `[7, 5, 3]` → up
- Diagonal sum 3: `[6, 8]` → down
- Diagonal sum 4: `[9]` → up

### Example 2

```
Input:
2 2
1 2
3 4

Output:
1 2 3 4
```

## Function Signature

```
(solve m n grid)
```

- `m`, `n` — dimensions of the matrix (positive integers).
- `grid` — a vector of `m` rows, each row being a vector of `n` integers.

## Input / Output Convention

The harness reads case data from a single `CASE0` environment variable in this format:

```
CASE0="<m> <n>
<row 1 values>
<row 2 values>
...
<row m values>"
```

You should print the diagonal traversal as space-separated values on one line, terminated by a newline.

## Notes

- `1 <= m, n <= 100`, element values fit in 32-bit signed integers.
- You may output trailing spaces or a trailing newline; both are accepted.
- A common approach is to iterate `s` from `0` to `m + n - 2` and, for each `s`, collect the pair `(i, j) = (max(0, s - n + 1), min(s, n - 1))` while `i < m` and `j >= 0`, then reverse the order when `s` is even.
