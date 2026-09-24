# Car Pooling

## Problem

You are driving a vehicle that has a fixed passenger **capacity**. There is a planned trip described as a sequence of `n` smaller rides. Each ride is an interval `[start, end)` on a one‑dimensional route (e.g. a highway or a single bus line) together with a number of passengers that board at `start` and leave at `end`.

All rides share the same route, so at any point `p` on the route the passengers currently in the vehicle are exactly those rides with `start ≤ p < end`. The vehicle starts and ends the trip empty.

Determine whether it is possible to complete the entire trip **without ever exceeding the vehicle's capacity**.

## Input

The input is provided as a single block of lines following the convention:

```
CASE0=<n>
CASE0_CAPACITY=<capacity>
CASE0_TRIP_0=<start>,<end>,<passengers>
CASE0_TRIP_1=<start>,<end>,<passengers>
...
```

- `n` — number of rides (`1 ≤ n ≤ 10^5`).
- `capacity` — maximum number of passengers the vehicle can hold (`1 ≤ capacity ≤ 10^9`).
- For each ride `i`: integers `start`, `end`, `passengers` (`0 ≤ start < end ≤ 10^9`, `1 ≤ passengers ≤ capacity`).

Coordinates and counts fit comfortably in 64‑bit signed integers.

## Output

Print `YES` if the trip can be completed without exceeding capacity, otherwise print `NO`.

## Example

```
CASE0=3
CASE0_CAPACITY=4
CASE0_TRIP_0=1,5,2
CASE0_TRIP_1=2,4,3
CASE0_TRIP_2=5,9,3
```

Output:
```
YES
```

## Function Signature (suggested)

```clojure
(solve n capacity trips) ; => "YES" | "NO"
```

where `trips` is a vector/sequence of `[start end passengers]` triples.

## Notes

- Treat every coordinate as an integer point; rides are half‑open `[start, end)`, so passengers from a ride ending at `x` do **not** count against rides starting at `x`.
- The classic sweep‑line / event‑point approach processes the `2n` events `(pos, +passengers)` for pickups and `(pos, -passengers)` for drop‑offs, scanning positions in non‑decreasing order and tracking the running total.
- An event sweep with a min‑heap is not required; a sorted event list with a running sum is enough, but a priority queue solution is also acceptable.
- Watch out for events at the same position: drop‑offs should be applied **before** pickups at the same coordinate, given the half‑open convention.
