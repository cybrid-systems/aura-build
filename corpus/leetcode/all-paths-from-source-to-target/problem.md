# All Paths From Source to Target

## Problem

You are given a **directed acyclic graph (DAG)** with `n` nodes, labeled `0` to `n-1`. The graph is represented by an adjacency list `graph`, where `graph[i]` is a list of all nodes you can travel to directly from node `i` (edges point from `i` to each node in `graph[i]`).

Find **all possible simple paths** from node `0` to node `n-1` and return them. You may return the paths in any order, but each path must be a list of node indices in traversal order, and the collection must contain every valid path exactly once.

The DAG has no cycles, so there are finitely many source-to-target paths.

## Function Signature

```clojure
(solve graph)
```

- `graph` — a vector of vectors of non-negative integers, where `graph[i]` is the list of neighbors reachable from node `i`. Node `0` is the source and node `(n-1)` is the target, with `n = (count graph)`.

**Returns:** a vector of vectors, where each inner vector is a path from `0` to `n-1` represented as a sequence of node indices.

## Input Convention

The harness reads a single test case from the file `case.in` using the format described below. Your `solve` function receives the parsed value directly.

```
CASE0=graph
```

For example:

```
CASE0=[[1,2],[3],[3],[]]
```

This describes a 4-node DAG:
- from `0` you can go to `1` or `2`,
- from `1` you can go to `3`,
- from `2` you can go to `3`,
- from `3` has no outgoing edges (it is node `n-1`).

The expected return is `[[0,1,3],[0,2,3]]` (order of paths may vary).

## Notes

- A valid path starts at `0`, ends at `n-1`, and every consecutive pair of nodes corresponds to a directed edge in the graph.
- Cycles cannot occur because the input is guaranteed to be a DAG, so simple DFS / backtracking suffices without a visited-set guard against revisits.
- Each path in the output must contain node `0` as its first element and node `n-1)` as its last element; no path may be empty.
