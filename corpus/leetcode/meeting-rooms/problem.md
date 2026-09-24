# Meeting Rooms

## Problem Statement

You are given an array of meeting time intervals, where each interval is represented as a pair of integers `[start, end]`. A single person wants to attend **all** of these meetings. Determine whether it is possible for them to do so, given that any two meetings must not overlap in time (the end of one meeting must be less than or equal to the start of the next — touching intervals are considered non-overlapping).

Return `True` if the person can attend all meetings, and `False` otherwise.

## Input

- The first line contains a single integer `N`, the number of meetings (`0 ≤ N ≤ 10^5`).
- The next `N` lines each contain two integers `start` and `end` (`0 ≤ start < end ≤ 10^9`), representing one meeting interval.

## Output

- Print `true` if all meetings can be attended without overlap, otherwise print `false`.

## Function Signature (Aura)

```clojure
(solve n intervals)
```

Where:

- `n` — the number of meetings (integer).
- `intervals` — a vector of `[start end]` pairs, length `n`.

Return `true` or `false`.

## I/O Convention (CASE0)

```
CASE0=
3
0 30
5 10
15 20
```

Expected output:

```
false
```

## Notes

- Sort the intervals by their start time and check whether any consecutive pair overlaps (`intervals[i].end > intervals[i+1].start`).
- The naive O(N^2) pairwise check is too slow for `N` up to 10^5; aim for O(N log N) after sorting.
- A single meeting (`N = 1`) is always attendable; an empty schedule (`N = 0`) is trivially attendable.
- Interval bounds are inclusive at the start and exclusive at the end, so `[0, 5)` and `[5, 10)` do **not** overlap.
