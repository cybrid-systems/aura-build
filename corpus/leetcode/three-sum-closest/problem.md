# 3Sum Closest

## Problem

Given an integer array `nums` of length `n` and an integer `target`, find the sum of three integers in `nums` such that the sum is **closest to** `target`. Return that sum.

You may assume that there is exactly **one** solution for each test case (the closest sum is unique).

## Function Signature

```lisp
(solve nums target)
```

- `nums` — a list of integers (length ≥ 3, possibly with negatives and duplicates).
- `target` — an integer.
- **Returns** the integer sum of the chosen triple that is closest to `target`.

## Input Convention

The harness feeds parameters via `CASE0` / `CASE1` lines, each containing two whitespace-separated fields:

```
CASE0=1 2 5 6 8 11 ; target=13
CASE1=-1 2 1 -4 ; target=1
```

- The leading field (before the first space) is the list of integers.
- The field after `target=` is the integer target.
- You may receive multiple `CASE` lines; process them independently and output one result per line, in order.

## Output Convention

Print one integer per case — the closest sum — on its own line:

```
13
2
```

## Notes

- Sorting the array lets a two-pointer sweep solve the problem in **O(n²)** time.
- Track the running best using `abs(best - target)` as the comparison key; update whenever a strictly smaller distance is found.
- The output is the actual sum, **not** its distance from `target`.
