# Minimum Number of Arrows to Burst Balloons

## Problem

There are some spherical balloons spread out on a flat 2D plane. Each balloon is described by a horizontal interval `[x_start, x_end]` (endpoints inclusive), meaning the balloon spans that range on the x-axis. An arrow can be shot vertically (along the y-axis) at any x-coordinate. An arrow at position `x` bursts every balloon whose interval contains `x`.

Given a list of balloon intervals, determine the **minimum number of arrows** required to burst every balloon.

You may assume that `1 <= len(points) <= 10^5`, coordinates fit in 32-bit signed integers, and `x_start <= x_end`.

## Function Signature

```python
def solve(points: list[tuple[int, int]]) -> int:
    ...
```

## Input / Output Convention

This problem is run through the **Aura** harness. There is no stdin. The harness invokes your `solve` function directly.

A typical case is configured in `aura.json` (or an equivalent config block) like:

```
CASE0=points=[[10,16],[2,8],[1,6],[7,12]]
CASE1=points=[[1,2],[3,4],[5,6],[7,8]]
CASE2=points=[[1,2],[2,3],[3,4],[4,5]]
```

For each case, the harness sets up the input list `points` and expects `solve(points)` to return the minimum number of arrows needed.

## Notes

- Sort the intervals by their right endpoint — this is the key insight for the greedy approach.
- Two balloons can be burst by the same arrow if and only if their intervals overlap (i.e., share some x-coordinate). Shooting an arrow at the rightmost possible shared x-coordinate is optimal.
- The greedy strategy is optimal: repeatedly pick the right endpoint of the earliest-finishing remaining balloon, shoot an arrow there, and skip every balloon that interval contains that point.
- Time complexity `O(n log n)` from sorting is sufficient for `n = 10^5`.
