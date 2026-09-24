# Bipartite Graph

## Problem

You are given an undirected graph with `n` vertices and `m` edges. Determine whether the graph is **bipartite**, i.e., whether its vertices can be split into two disjoint sets such that every edge connects a vertex from one set to a vertex from the other set.

The graph may be disconnected, so each connected component must be checked independently.

A graph is bipartite if and only if it contains no odd-length cycle, which can be detected by attempting to 2-color the vertices: assign each vertex a color (say, `0` or `1`) such that every edge connects vertices of different colors. A BFS or DFS from each unvisited vertex can be used for this.

Return `YES` if the graph is bipartite, otherwise `NO`.

## Input

The input consists of multiple test cases. The first line contains a single integer `T`, the number of test cases.

For each test case:
- A line with two integers `n` and `m` (`1 ≤ n ≤ 10^5`, `0 ≤ m ≤ 2·10^5`) — the number of vertices and edges.
- `m` lines follow, each containing two integers `u` and `v` (`1 ≤ u, v ≤ n`) describing an undirected edge.

The sum of `n` over all test cases does not exceed `10^5`, and the sum of `m` over all test cases does not exceed `2·10^5`.

## Output

For each test case, output a single line containing `YES` if the graph is bipartite, or `NO` otherwise.

## Example

### Input
```
CASE0=2
3 3
1 2
2 3
1 3
4 3
1 2
2 3
3 4
```

### Output
```
CASE0=NO
YES
```

## Notes

- Use BFS or DFS starting from every unvisited vertex; isolated vertices (with degree `0`) are trivially bipartite.
- If during BFS/DFS an edge connects two vertices already assigned the same color, the graph is not bipartite.
- An adjacency list with `O(n + m)` total memory is sufficient.

## Function Signature (Haskell)

```haskell
solve :: Int -> Int -> [(Int, Int)] -> Bool
-- Returns True if the graph is bipartite, False otherwise.
```

In the harness, each test case supplies `n`, `m`, and the list of edges; the solver returns whether the graph is bipartite, and the wrapper prints `YES`/`NO` accordingly.
