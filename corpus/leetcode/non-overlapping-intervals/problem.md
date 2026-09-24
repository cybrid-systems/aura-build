# Non-overlapping Intervals

## Problem

You are given a list of `n` intervals, each represented as a pair `[start, end]`. Two intervals `[a, b]` and `[c, d]` are considered **overlapping** if they share any point in time, i.e. `a < c` and `c < b` (equivalently, their interiors intersect, including endpoint-touching cases depending on the chosen convention — here we use strict overlap: intervals `[1,2]` and `[2,3]` do **not** overlap).

Your task is to remove the **minimum number of intervals** so that no two remaining intervals overlap.

## Function Signature

```python
def solve(intervals: list[list[int]]) -> int:
    """Return the minimum number of intervals to remove."""
```

## Input

The input is provided as a single block on stdin, but for the Aura harness we expose it via the `CASE0` constant. The harness writes a single test case using the following convention:

```
CASE0=
1 2
2 3
3 4
```

- The first line is the header `CASE0=` (no value expected after `=` on this line; the harness parses the lines that follow).
- Each subsequent line contains two integers `start end` representing one interval.
- There is no count line; the number of intervals is inferred from the number of lines following the header.
- Intervals may be given in any order.

## Output

A single integer: the minimum number of intervals to remove so that the remaining intervals are pairwise non-overlapping.

## Examples

### Example 1
Input (via `CASE0`):
```
1 2
2 3
3 4
```
Output:
```
0
```
All intervals are already non-overlapping (endpoints touch but do not overlap).

### Example 2
Input:
```
1 2
1 3
2 3
3 4
```
Output:
```
1
```
Removing any one of the first three intervals makes the rest non-overlapping.

## Notes

- An empty input (no interval lines after the header) should return `0`.
- Sorting the intervals by their end coordinate and greedily keeping the interval with the earliest end time yields an optimal solution: an interval-scheduling classic.
- Time complexity `O(n log n)` from the sort is easily fast enough for typical constraints.
