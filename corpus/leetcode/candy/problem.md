# Candy

## Problem

There are `N` children standing in a line, each with an associated rating. You must give each child at least one candy, while also satisfying the rule that any child whose rating is **strictly greater** than an immediate neighbor must receive **strictly more** candies than that neighbor.

Given the ratings array, compute the **minimum total number of candies** that must be distributed.

## Function Signature

```lisp
(defun solve (ratings)
  ;; returns minimum total candies as an integer
  )
```

## Input

The input is provided as `CASE0=...` lines on standard input. Each `CASE0` is a list literal (whitespace- or comma-separated) of integer ratings, one case per line.

Example:

```
CASE0=(1 0 2)
CASE0=(1 2 2 4 3)
CASE0=(4 3 2 1)
```

- `0 <= N <= 10000`
- `0 <= rating[i] <= 10000`

## Output

For each `CASE0` line, print one line containing the minimum total number of candies needed.

## Notes

- An empty list yields a total of `0` candies.
- The greedy approach uses two passes (left-to-right and right-to-left) to derive the minimum per-child candy counts in **O(N)** time.
