# Merge Intervals

## Problem

Given a list of intervals where each interval is a pair `[start, end]` (with `start <= end`), merge all overlapping intervals and return a list of non-overlapping intervals that cover all the input points.

Two intervals `[a, b]` and `[c, d]` are considered overlapping (and should be merged) if they share at least one point, i.e. when `a <= d` and `c <= b`. Intervals that only touch at the boundary (e.g. `[1, 2]` and `[2, 3]`) **are** considered overlapping and should be merged into `[1, 3]`.

The output list must be sorted by the `start` coordinate of each interval and contain no intervals that overlap with each other.

## Function Signature

```haskell
solve :: [(Int, Int)] -> [(Int, Int)]
```

- Input: a list of intervals, each represented as a `(start, end)` tuple. The list may be in any order, may contain duplicate intervals, and may be empty.
- Output: a list of merged, non-overlapping intervals sorted by their start value.

## Input / Output Convention

The program reads no input from stdin. Instead, the harness fixes the following examples via `main` (each preceded by a `CASE` marker):

```
CASE0=input: [(1,3),(2,6),(8,10),(15,18)] | expected: [(1,6),(8,10),(15,18)]
CASE1=input: [(1,4),(4,5)] | expected: [(1,5)]
CASE2=input: [(1,4),(0,4)] | expected: [(0,4)]
CASE3=input: [] | expected: []
CASE4=input: [(1,4),(2,3)] | expected: [(1,4)]
```

The driver invokes `solve` on the `input` portion of each case and compares the result against `expected` using structural equality on the list of `(Int, Int)`.

## Notes

- Edge cases to keep in mind: empty input, single interval, intervals that share an endpoint, fully nested intervals, and intervals already in sorted order vs. reverse order.
- An efficient approach runs in `O(n log n)` time (sorting dominates). A naive scan-based solution also works for small inputs.
- You may assume all coordinates fit comfortably in `Int`.
