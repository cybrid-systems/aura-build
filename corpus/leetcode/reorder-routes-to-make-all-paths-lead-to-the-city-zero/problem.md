# Reorder Routes to Make All Paths Lead to the City Zero

## Problem

There are `n` cities numbered from `0` to `n - 1` and `n - 1` directed roads such that there is exactly one way to travel between any two cities (i.e., the roads form a rooted tree structure, rooted at city `0`). Each road is described by two integers `u` and `v` indicating a one-way road from `u` to `v`.

In one operation, you may reverse the direction of a single road. Find the **minimum number of operations** required so that, starting from any city, it is possible to reach city `0` by following the roads. Equivalently, after the reversals, every directed road should point *toward* city `0`.

## Input

The input is provided directly as function arguments:

- `n` — number of cities (`2 ≤ n ≤ 5 * 10^4`)
- `edges` — a list of `n - 1` pairs `[u, v]` representing a directed road from `u` to `v`

## Output

Return a single integer: the minimum number of roads that must be reversed.

## Function Signature

```python
def solve(n: int, edges: list[list[int]]) -> int:
    ...
```

## Example

```
n = 6
edges = [[0,1],[1,3],[2,3],[4,3],[5,4]]
CASE0_ANSWER = 3
```

## Notes

- The underlying graph is a tree; a single DFS/BFS from city `0` is enough.
- An edge `u -> v` must be reversed iff, while traversing from `0`, we discover a neighbor `v` via this edge (i.e., the edge points *away* from `0`).
- Use the adjacency representation `(neighbor, needs_reversal_flag)` to count the reversals in one pass.
