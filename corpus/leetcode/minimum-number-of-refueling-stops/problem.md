# Minimum Number of Refueling Stops

## Problem

A car starts at position `0` with some initial amount of fuel and wants to reach a target position `target` (target > 0). The car consumes one unit of fuel per unit of distance traveled.

There are `n` fuel stations along the way. Each station `i` is described by:
- `stations[i][0]` — the position of the station (distance from start, 0 < position < target)
- `stations[i][1]` — the amount of fuel available at that station

Stations are given in strictly increasing order of position.

Determine the **minimum number of refueling stops** the car must make to reach `target`. If `target` cannot be reached, return `-1`.

Assume the car has an unlimited fuel tank capacity.

## Function Signature

```clojure
(defn solve [target start-fuel stations]
  ;; target: long
  ;; start-fuel: long
  ;; stations: vector of [position fuel] pairs, sorted by position
  ;; returns: long
  )
```

## Input Convention (Aura harness, no stdin)

The harness invokes your `solve` function with arguments read from a `CASE0` block in the problem source. Lines are whitespace-separated tokens of the form:

```
CASE0=target,start-fuel,n
CASE0a=pos0,fuel0
CASE0b=pos1,fuel1
...
```

For example:

```
CASE0=100,10,4
CASE0a=10,20
CASE0b=20,30
CASE0c=30,40
CASE0d=60,50
```

Your `solve` function is then called with `target=100`, `start-fuel=10`, and `stations=[[10 20] [20 30] [30 40] [60 50]]`. The expected return value for this case is `2` (e.g., stop at station 2 for 30 fuel and station 3 for 40 fuel — or any optimal pair).

## Notes

- The positions of stations are sorted in strictly increasing order, and every station position is strictly greater than `0` and strictly less than `target`.
- A classic greedy approach uses a max-heap of fuel amounts from stations already passed but not yet used; when fuel runs low, pop the largest fuel from the heap and refuel there.
- If the heap is empty before reaching `target`, return `-1`.
- Return `-1` if `start-fuel` alone is insufficient to reach the first station (or `target` when `n = 0`).
