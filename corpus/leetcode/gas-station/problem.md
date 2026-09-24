# Gas Station

## Problem

There are **N** gas stations arranged in a circle. At station `i` (0-indexed), you can fill `gas[i]` units of fuel, and traveling to the next station costs `cost[i]` units of fuel (`cost[N-1]` is the cost to return to station `0`).

A truck starts with an **empty tank** at some station and must visit every station exactly once, returning to the starting station. The tank has unlimited capacity, but it can never hold negative fuel.

Determine whether there exists a starting station such that the journey is possible. If one exists, return its index; otherwise, return `-1`.

The answer, when it exists, is **guaranteed to be unique**.

## Function Signature

```lisp
(defun solve (gas cost)
  ;; returns: integer (starting index, or -1)
  )
```

## Input Format

The input is provided as plain text on standard input, using the Aura `CASE0` convention.

```
CASE0=<case_id>
N=<number_of_stations>
GAS=<space-separated gas amounts, length N>
COST=<space-separated cost amounts, length N>
```

For example:

```
CASE0=0
N=3
GAS=1 2 3
COST=2 1 0
```

You should ignore everything except the fields needed. There may be multiple `CASE` blocks in extended versions; handle only `CASE0`.

## Output Format

Print the answer as a single integer on one line.

```
3
```

(or `-1` if no valid starting station exists).

## Notes

- **Constraints:** `1 ≤ N ≤ 10^5`, `0 ≤ gas[i], cost[i] ≤ 10^4`. A solution must run in `O(N)` time.
- **Key observation:** If the total fuel available is at least the total cost, a starting station exists. The classic linear-scan trick locates it in one pass by tracking the running tank minimum.
