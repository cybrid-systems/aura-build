# Interval List Intersections

## Problem

You are given two lists of **closed** intervals, where each list is already sorted by start time and contains **non-overlapping** intervals that are also non-adjacent (the end of one interval is strictly less than the start of the next).

Your task is to compute the intersection of the two interval lists — i.e., all intervals `[l, r]` such that `l` and `r` appear as a sub-range in both lists.

The output must be a list of disjoint, sorted intersections. If two intersections touch at a single point (e.g., `[1,2]` and `[2,3]`), **merge them** into a single interval `[1,3]` because the input intervals are closed.

If there is no intersection, return an empty list.

## Function Signature

```clojure
(defn solve [a b] ...)
```

- `a` and `b` are vectors of `[start end]` pairs (integers, `start <= end`).
- Return a vector of `[start end]` pairs representing the merged intersections, in order.

## Input / Output

The harness reads one case from the file `CASE0` written as plain Lisp-like data:

```
CASE0 = [["0 2","5 10","13 23","24 25"],["1 5","8 12","15 24","25 26"]]
```

- The outer list has two elements: the two interval lists.
- Each interval is encoded as a string `"start end"` with a single space.
- Each inner list is a JSON-like array of those strings.

You should output the result by `prn`-ing a vector of `[start end]` pairs (numbers), e.g.:

```
[[1 2] [5 5] [10 10] [15 23] [24 24] [25 25]]
```

(The numbers and brackets are the standard Clojure printed form.)

## Notes

- Use the **two-pointer** technique: advance whichever pointer has the smaller `end`.
- Intersections that share a boundary should be merged.
- Time complexity should be `O(n + m)`, where `n` and `m` are the lengths of the two lists.
- The harness will parse your printed vector; keep the output on a single line.
