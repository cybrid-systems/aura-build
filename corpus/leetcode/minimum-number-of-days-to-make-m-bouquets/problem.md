# Minimum Number of Days to Make m Bouquets

## Problem

You are given an integer array `bloomDay`, where `bloomDay[i]` denotes the day on which the `i`-th flower blooms. You also have two integers `m` and `k`.

To make a bouquet, you must pick exactly `k` **adjacent** flowers from the garden, and all of them must already be bloomed on the chosen day. A flower can belong to **at most one** bouquet.

Determine the **minimum** day `d` such that it is possible to make **at least** `m` bouquets using flowers that have bloomed by day `d`. If it is impossible, return `-1`.

## Function Signature

```lisp
(defun solve (bloom-day m k)
  ;; returns: integer (minimum day, or -1 if impossible)
  )
```

## Input Format

The harness feeds the function directly; no `STDIN` is read. However, equivalent test cases follow this layout on `STDIN`:

```
CASE0=bloomDay = [1, 10, 3, 10, 2], m = 3, k = 1
CASE1=bloomDay = [1, 10, 3, 10, 2], m = 3, k = 2
CASE2=bloomDay = [7, 7, 7, 7, 12, 7, 7], m = 2, k = 3
```

Each `CASEn=` line describes one independent invocation: a vector/list `bloomDay`, an integer `m`, and an integer `k`.

## Output Format

The function returns an integer answer per call. For a `STDIN`-style harness, print one integer per case in order:

```
3
-1
12
```

## Constraints

- `1 <= bloomDay.length <= 10^5`
- `1 <= bloomDay[i] <= 10^9`
- `1 <= m <= 10^5`
- `1 <= k <= bloomDay.length`

## Notes

- It is impossible when `m * k > bloomDay.length`; return `-1` immediately.
- The answer lies in the range `[min(bloomDay), max(bloomDay)]`; binary search on the day value and, for each candidate day, greedily scan to count how many disjoint groups of `k` adjacent bloomed flowers can be formed.
- Watch for the off-by-one: a flower consumed by one bouquet cannot be reused, so reset the run-length counter whenever an unbloomed flower is encountered, and reset after each completed bouquet.
