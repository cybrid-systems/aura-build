# Smallest Number Range

## Problem

You are given `k` sorted (in non-decreasing order) lists of integers, each of length `n`. A **range** `[a, b]` is said to cover a list if there exists at least one element from that list lying in `[a, b]` (inclusive). Your task is to find the smallest range `[a, b]` that covers **all `k` lists simultaneously**.

The "smallness" of a range is determined by its length `b - a`. If multiple ranges have the same minimum length, choose the one with the smallest starting value `a`.

## Input

The input is provided on standard input, but for this harness we use a fixed `CASE0` format. The first line contains two integers `k` and `n`. Then `k` lines follow, each containing `n` integers (a sorted list).

```
CASE0=
3 5
1 5 10 13 21
2 6 12 19 25
3 8 15 24 26
```

The result line is **not** part of the input — only the data above is fed in. Your `solve` function must return the answer as two integers `a b` (printed by the harness).

## Output

Print the two integers `a` and `b` on a single line, separated by a space, representing the smallest range.

```
1 5
```

(For the sample above, the smallest range is `[1, 5]`, which contains `1` from list 1 and `2`, `3` from the other two lists; length 4, the minimum possible.)

## Function Signature

```clojure
(solve k n lists) ;; returns [a b]
```

- `k` — number of lists
- `n` — length of each list
- `lists` — a vector of `k` vectors, each of length `n`, sorted in non-decreasing order

## Notes

- A min-heap of size `k` holding the current element from each list (plus its list index and position) gives an `O(k * n * log k)` solution.
- An `O(k * n)` solution exists using a sliding window / pointer technique across the merged sorted traversal.
- Edge case: `k == 1` — the answer is `[lists[0][0], lists[0][0]]`.
