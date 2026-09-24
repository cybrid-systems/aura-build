# Network Delay Time

## Problem

You are given a directed weighted graph representing a network of `n` nodes (labeled `1..n`) and `times` — a list of directed edges `times[i] = (u, v, w)` meaning that a signal traveling from node `u` to node `v` takes `w` units of time.

A signal is sent from a starting node `k`. All edges send signals **in parallel**. Return the minimum number of time units required for the signal to reach **every** reachable node. If it is impossible for the signal to reach all nodes, return `-1`.

The "time to reach all nodes" is defined as the maximum of the shortest-path distances from `k` to every other node (for nodes that are reachable from `k`).

## Function Signature

```python
def solve(n: int, times: list[tuple[int, int, int]], k: int) -> int:
    ...
```

## Input Convention (CASE lines)

The harness invokes your function with a single case. Results are written to **CASE0=...** lines.

Example input block:

```
CASE
n=3
times=[(1,1,0),(1,2,1),(2,3,1)]
k=1
```

Example valid output:

```
CASE0=2
```

Another example (unreachable node):

```
CASE
n=2
times=[(1,2,1)]
k=2
```

Output:

```
CASE0=-1
```

## Notes

- `1 <= n <= 100`, `times` length up to `n*(n-1)`; edge weights `w` are non-negative integers.
- Edges may include self-loops and duplicate edges; treat each edge independently.
- Use Dijkstra's algorithm (or BFS with a priority queue) over a weighted adjacency list. A simple BFS is **not** sufficient because weights are non-negative but not necessarily uniform.
- A self-loop `(u, u, 0)` does not affect the shortest distance to `u`, but should not cause incorrect behavior.
- The answer is the maximum of `dist[i]` over all `i != k` for which `dist[i]` is finite; return `-1` if any node is unreachable.
