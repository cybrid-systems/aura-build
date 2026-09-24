# Average of Levels in Binary Tree

## Problem Statement

Given the root of a binary tree, return the average value of the nodes at each level of the tree as a list of floating point numbers. The average for a level is the sum of its node values divided by the number of nodes at that level.

The tree node structure is:

```
node := { val: int, left: node | nil, right: node | nil }
```

The tree contains at least one node. Values fit in a standard signed 32-bit integer range, but the computed average may be non-integer, so output must preserve fractional precision (at least 5 decimal places).

## Function Signature

```
solve(root: Node) -> list[float]
```

## Input Convention (CASE format)

The Aura harness provides the tree on a single input line as a **CASE0** payload. Each line is one test case:

```
CASE0=<level-order-representation>
```

The level-order representation uses `null` for missing children and is space-separated. For example:

```
CASE0=3 9 20 null null 15 7
CASE0=1 null 2
CASE0=-1 null 2 null 3 null 4 null 5
```

Your function must read `CASE0=...` from standard input, parse the level-order sequence into the binary tree, and return the list of per-level averages.

## Output Convention

Print one line per test case containing the averages for each level, separated by a single space and formatted to at least 5 decimal places. If there are multiple cases, repeat the input read loop accordingly (the harness typically supplies exactly one `CASE0=...` line per run).

Example output for `3 9 20 null null 15 7`:

```
3.00000 14.50000 11.00000
```

## Notes

- A breadth-first traversal naturally gives per-level groups; a depth-first traversal also works if you track depth and accumulate per-level sums/counts.
- The tree is guaranteed non-empty, so the result list has at least one element.
- Use floating point division; do not integer-divide, or shallow trees like `0 0 0 0 0 ...` will produce incorrect results.
- `null` entries in the level-order input represent absent children and are not counted toward any level's node count.
