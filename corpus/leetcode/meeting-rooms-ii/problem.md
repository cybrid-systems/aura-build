# Meeting Rooms II

## Problem Statement

Given an array of meeting time intervals where `intervals[i] = [start_i, end_i]`, determine the **minimum number of conference rooms** required to schedule all meetings without any conflicts.

Two meetings conflict if they overlap in time — that is, if one starts before the other ends (intervals sharing an endpoint like `[1, 4]` and `[4, 6]` do **not** conflict).

### Examples

**Example 1**
```
Input:  [[0, 30], [5, 10], [15, 20]]
Output: 2
Explanation: Meeting [0,30] needs one room; [5,10] and [15,20] can share a second.
```

**Example 2**
```
Input:  [[7, 10], [2, 4]]
Output: 1
Explanation: No overlap; one room suffices.
```

**Example 3**
```
Input:  [[1, 4], [4, 6], [4, 7]]
Output: 2
```

## Function Signature

Write a function `solve` with the following signature:

```
(defn solve [intervals] ...)
```

- `intervals` — a vector of `[start, end]` pairs (inclusive start, exclusive end). Endpoints are integers; `start < end` is guaranteed (in standard cases) but the function should be robust.
- Returns the **minimum number of rooms** required as a non-negative integer.

## I/O Convention

Input is read from standard input as a single line:

```
CASE0=[[0,30],[5,10],[15,20]]
```

- The payload is the JSON-like list of intervals appearing after `CASE0=`.
- Output a single integer on one line.

### Sample Session

```
> CASE0=[[0,30],[5,10],[15,20]]
> 2
```

## Notes

- **Brute force**: for each interval, check overlaps against all currently active meetings → O(n²). Acceptable for `n ≤ ~2000`.
- **Optimal**: separate `start` and `end` time arrays; sort both, then sweep with two pointers counting concurrent meetings → O(n log n).
- **Alternative optimal**: maintain a min-heap of meeting end times; evict the earliest-ending meeting whose end ≤ current start. Peak heap size = answer → O(n log n).
- Edge case: empty input or `[]` should return `0`.
- Half-open interval semantics: `[1, 4]` and `[4, 6]` do **not** overlap.
