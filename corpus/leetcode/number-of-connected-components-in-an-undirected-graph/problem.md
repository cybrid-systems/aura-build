# Number of Connected Components in an Undirected Graph

## Problem

You are given an undirected graph with `n` nodes labeled from `0` to `n - 1`. Some pairs of nodes are connected by edges. Two nodes belong to the same **connected component** if there is a path of edges between them. Your task is to determine the total number of connected components in the graph.

## Input

Input is provided as plain text on standard input in the following form:

```
CASE0=10
CASE1=5 4
0 1
1 2
2 3
3 4
```

Each case begins with a header line of the form `CASEx=...`, where `x` is the case index (starting at `0`). The value(s) after the `=` specify the parameters of that test case.

- The first value after `CASE0=` is `n`, the number of nodes.
- For subsequent cases (`CASE1`, `CASE2`, ...), the values after the first `=` form the edge list. The first of these is the number of edges `m`, followed by `2 * m` integers representing the endpoints of each edge.

A single value `n` with no following lines indicates a graph with `n` nodes and no edges.

## Output

For each case, print a single line containing the number of connected components.

## Function Signature

```
solve(n: int, edges: list[tuple[int, int]]) -> int
```

## Constraints

- `1 <= n <= 1000`
- `0 <= m <= n * (n - 1) / 2`
- `0 <= u, v < n`

## Notes

- Use Union-Find (Disjoint Set Union with path compression and union by rank/size) for an efficient `O((n + m) * α(n))` solution.
- Initially, every node is its own component, so the count starts at `n` and decreases by `1` for each successful union operation between two different sets.
