# Matrix Chain Multiplication

## Problem

Given a sequence of matrices `A_1, A_2, ..., A_n`, where matrix `A_i` has dimensions `p[i-1] x p[i]` for an array of positive integers `p`, determine the minimum number of scalar multiplications required to compute the product `A_1 * A_2 * ... * A_n`.

The matrices cannot be reordered, only parenthesized. Your task is to compute the optimal parenthesization cost.

### Function Signature

```lisp
(defun solve (p)
  ;; returns minimum scalar multiplications as an integer
  )
```

- `p`: a list of `n+1` positive integers representing matrix dimensions, where matrix `i` has rows `p[i-1]` and columns `p[i]` (length of `p` is between 2 and 100, each value between 1 and 1000).

### Input Format

Input is provided via `*standard-input*` in the following form:

```
CASE0=<n>
CASE0=<p[0]> <p[1]> <p[2]> ... <p[n]>
```

- Line 1: `CASE0=<n>`, where `n` is the length of the dimension array (so there are `n-1` matrices).
- Line 2: `CASE0=<p[0]> <p[1]> ... <p[n]>`, space-separated positive integers for the dimension array `p`.

### Output Format

Print a single integer: the minimum number of scalar multiplications needed to multiply the chain.

```
CASE0=<answer>
```

### Notes

- The classic solution uses dynamic programming with cost `dp[i][j] = min over k of (dp[i][k] + dp[k+1][j] + p[i-1]*p[k]*p[j])` for `i <= k < j`.
- For a chain of length 1, the cost is 0 (no multiplication needed).
- Time complexity should be at most O(n^3).
