# Set Matrix Zeroes

## Problem

You are given an `M × N` matrix of integers. If any element in the matrix is `0`, its entire row and entire column must be set to `0`. Perform this transformation **in-place** — modify the input matrix directly rather than allocating a separate output matrix.

The operation must be stable with respect to cascading zeros: once a row or column is zeroed, the zeros it produces should not trigger additional zeroing beyond the original "source" rows and columns.

Implement an algorithm that uses **O(1)** extra space (beyond the input matrix itself) and runs in **O(M·N)** time.

## Function Signature

```
(solve [matrix] [m] [n] ...)
```

- `matrix` — a flat sequence of `m * n` integers representing the matrix in row-major order.
- `m` — number of rows (1 ≤ m ≤ 1000).
- `n` — number of columns (1 ≤ n ≤ 1000).

Return / output the modified flat sequence representing the zeroed matrix in row-major order.

## Input / Output Convention (CASE0)

Each test case is provided on stdin using the `CASE0=` format:

```
CASE0=matrix=[1,2,3,4,0,6,7,8,9,10,11,12]&m=3&n=4
EXPECT0=[1,0,3,0,0,0,0,0,9,0,11,0]
```

- `matrix=` is a comma-separated list of integers (row-major).
- `m=` and `n=` give the dimensions.
- Multiple cases may appear, separated by newlines or spaces.

## Notes

- A standard trick is to use the **first row** and **first column** as marker storage for which rows/columns contain a zero, then clear based on those markers — this achieves the O(1) auxiliary space requirement.
- Don't forget to handle the top-left corner cell carefully: it belongs to both the first row and first column markers.
- Edge case: if `m = 1` or `n = 1`, the matrix is a single row or column — handle it without index errors.
- Constraint: `m * n` may be up to `10^6`, so the solution must be linear and avoid quadratic blowups from naive copying.
