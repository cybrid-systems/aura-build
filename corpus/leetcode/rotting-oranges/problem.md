# Rotting Oranges

## Problem

You are given a 2D grid representing a room. Each cell can contain one of three values:

- `0` — an empty cell (nothing)
- `1` — a fresh orange
- `2` — a rotten orange

Every minute, any fresh orange that is **4-directionally adjacent** (up, down, left, right) to a rotten orange also becomes rotten.

Return the **minimum number of minutes** that must elapse until no fresh orange remains, or `-1` if it is impossible (some fresh orange can never be reached by the rot).

If there are no fresh oranges at the start, return `0`.

## Function Signature

```lisp
(defun solve (grid)
  ...)
```

- `grid` is a list of lists of integers (rows of the room).
- Return a single integer: the minimum minutes until rot completes, or `-1` if unreachable.

## Input / Output Convention (Aura harness)

The harness reads from a single test case in the following format:

```
CASE0=4
CASE0=1 2 0 1
CASE0=1 1 1 0
CASE0=0 1 1 1
CASE0=0 0 0 0
```

- Line 1: number of rows `n`.
- Lines 2..n+1: each row is space-separated integers.

Output a single integer — the answer for the test case.

### Example

Input:
```
CASE0=3
CASE0=2 1 1
CASE0=1 1 0
CASE0=0 1 1
```

Output:
```
4
```

## Notes

- Use **multi-source BFS**: enqueue every initially rotten orange as a source at time `0`, and expand in waves. Each BFS level corresponds to one minute.
- Track two counts while reading the grid: total fresh oranges and the number of cells newly rotted at each step. The answer is the elapsed minutes when the last fresh orange rots, or `-1` if any fresh orange is left over after BFS finishes.
- Constraints (typical): grid dimensions up to around `100 × 100`; a plain queue-based BFS is more than fast enough.
