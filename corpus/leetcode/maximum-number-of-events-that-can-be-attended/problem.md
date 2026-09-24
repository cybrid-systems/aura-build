# Maximum Number of Events That Can Be Attended

## Problem

You are given `n` events. Each event has a start day and an end day, inclusive: `[start, end]`. On any single day, you can attend at most one event. You may attend an event on any of the days in its interval, but each event only needs one day of attendance to count as attended.

Return the maximum number of events that can be attended.

## Function Signature

```clojure
(solve events)
```

- `events`: a sequence of `[start end]` pairs (1-indexed or 0-indexed days, but consistent within the input).
- Returns an integer: the maximum number of events you can attend.

## Input / Output Convention

Input is provided as `CASE0=` lines on stdin. A single case looks like:

```
CASE0=[[1,2],[2,3],[3,4]]
CASE0=ANS=3
```

The harness will call your `solve` function with the parsed vector of `[start end]` pairs. If `ANS=` is present, it is treated as the expected answer for self-check.

## Examples

Example 1
```
CASE0=[[1,2],[2,3],[3,4]]
CASE0=ANS=3
```
Explanation: Attend event 1 on day 1, event 2 on day 2, event 3 on day 3.

Example 2
```
CASE0=[[1,4],[4,4],[2,2],[3,4],[1,1]]
CASE0=ANS=4
```

Example 3
```
CASE0=[[1,100000]]
CASE0=ANS=1
```

## Notes

- `n` can be large (up to ~10^5) and day values can be large (up to ~10^9); prefer solutions that scale with the number of events rather than the day range.
- A standard greedy works: sort events by end day, and at each step attend the event on the earliest still-available day in its interval.
- Days may be 0-indexed or 1-indexed; your solution should be agnostic, or detect from the input range.
