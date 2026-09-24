# Insert Interval

## Problem

You are given a list of non-overlapping intervals `intervals` where each interval is a pair `[start, end]` with `start <= end`, and the list is sorted in ascending order by `start`. You are also given a single interval `newInterval = [start, end]`.

Insert `newInterval` into `intervals` so that the list remains sorted and contains no overlapping intervals. If the insertion causes overlaps with existing intervals, **merge** all touching/overlapping intervals into one. After merging, return the resulting list of intervals.

An interval `[a, b]` overlaps with `[c, d]` if `a <= d` and `c <= b` (i.e. they share any point, including touching endpoints).

## Function Signature

```
solve(intervals: list[list[int]], newInterval: list[int]) -> list[list[int]]
```

- `intervals` — sorted, non-overlapping list of intervals.
- `newInterval` — interval to insert.

Returns the merged list of intervals.

## Input Convention

The harness drives the solution directly (no stdin). A typical case description looks like:

```
CASE0=intervals=[[1,3],[6,9]], newInterval=[2,5]
CASE1=intervals=[[1,2],[3,5],[6,7],[8,10],[12,16]], newInterval=[4,8]
```

Each case provides `intervals` as a JSON-style list and `newInterval` as a JSON-style pair.

## Output

Return a `list[list[int]]` of merged intervals for each case.

## Notes

- The original `intervals` may be empty; in that case the result is just `[newInterval]` (possibly after merging only with itself).
- The result must be sorted by `start` and contain **no** overlapping intervals.
- A linear (`O(n)`) scan is sufficient and expected; no nested loops required.
- Endpoints are inclusive when checking for overlap, so merging `[1,4]` and `[4,7]` yields `[1,7]`.
