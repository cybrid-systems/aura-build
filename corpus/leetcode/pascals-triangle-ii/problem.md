# Pascal's Triangle II

Given an integer `k`, return the `k`-th row of Pascal's triangle (0-indexed).

Recall that Pascal's triangle is built so each interior element is the sum of the two elements directly above it, and each row begins and ends with `1`. For example, the first few rows are:

```
row 0: 1
row 1: 1 1
row 2: 1 2 1
row 3: 1 3 3 1
row 4: 1 4 6 4 1
```

## Input

A single non-negative integer `k`.

## Output

A single line with the `k`-th row printed as space-separated integers.

## Function Signature (harness hint)

```lisp
(defun solve (k) ...)
```

`K` is provided via the `K` variable (parsed from the case line). Return a list of integers representing the `k`-th row.

## I/O Convention (Aura harness)

- The harness reads one case per invocation.
- The case is exposed as `CASE0=...` style variables (here just `K`).
- The function `solve` should return the row as a Lisp list; the harness prints its elements space-separated.

## Examples

```
K=0  -> "1"
K=1  -> "1 1"
K=4  -> "1 4 6 4 1"
K=5  -> "1 5 10 10 5 1"
```

## Notes

- `0 <= k <= 30` is sufficient; the largest binomial coefficients fit comfortably in a standard 64-bit integer.
- Build the row iteratively in-place from the previous row (updating from right to left) to keep memory usage `O(k)`.
