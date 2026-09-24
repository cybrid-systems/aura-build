# Minimum Number of Meeting Rooms

You are given the start and end times of `n` meetings. Any two meetings that overlap in time cannot share the same room, but meetings whose intervals only touch at an endpoint (one ends exactly when another begins) may share a room. Determine the **minimum number of rooms** needed to schedule all meetings.

## Input
Each test case is provided as two lines on stdin:

```
CASE0=<n>
n=<n>
m=<comma-separated list of n start times>
m=<comma-separated list of n end times>
```

- `n` — number of meetings (1 ≤ n ≤ 10^5).
- Start and end times are non-negative integers given in **seconds**.
- A line `n=0` terminates input and is **not** processed.

## Output
For each test case, output one line containing the minimum number of meeting rooms required.

## Example

```
CASE0=3
n=3
m=0,5,15
m=30,10,20
```

Explanation: meetings are `[0,30]`, `[5,10]`, `[15,20]`. At time 0–10 two meetings overlap (`[0,30]` and `[5,10]`); at time 15–20 `[0,30]` still runs alongside `[15,20]`. Peak overlap is 2, so the answer is `2`.

## Function Signature (Aura)

```haskell
solve :: [(Int, Int)] -> Int
```

The harness passes the list of `(start, end)` pairs (already parsed from the `m=` lines) into `solve` and prints the returned value for each `CASE0=` block.

## Notes

- Two meetings `[a,b]` and `[c,d]` overlap iff `a < d` and `c < b`; back-to-back meetings (`b == c`) do not overlap.
- The expected approach is event-sweeping in O(n log n): sort start events and end events, increment a counter on each start while previous ends are still active, and decrement when an end is reached.
- Output one integer per test case, no extra formatting.
