# Graph Valid Tree

Given `n` nodes labeled from `0` to `n-1` and a list of `edges` where each edge is an undirected connection `[u, v]`, determine whether these nodes and edges form a valid tree.

A graph is a valid tree if and only if:
- It is **connected** (every node is reachable from every other node), and
- It is **acyclic** (contains no cycles).

Equivalently, a valid tree on `n` nodes must have exactly `n - 1` edges and be connected, or alternatively have exactly `n - 1` edges and be acyclic.

Your task is to return `true` if the given graph forms a valid tree, and `false` otherwise.

## Function Signature

```haskell
solve :: Int -> [(Int, Int)] -> Bool
```

- The first argument is the number of nodes `n`.
- The second argument is the list of undirected edges (each a pair `(u, v)`).
- Return `True` if the graph is a valid tree, `False` otherwise.

## Input Convention

The harness feeds input via lines in the following format:

```
CASE0=5
CASE0_EDGES=[[0,1],[0,2],[0,3],[1,4]]
```

- `CASE0=n` provides the number of nodes.
- `CASE0_EDGES=[[u1,v1],[u2,v2],...]` provides the edges as a JSON-style list of pairs.
- The expected output is a single line: `CASE0=True` or `CASE0=False`.

## Notes

- Assume `n >= 0`. For `n = 0`, the result is `True` (the empty graph is conventionally a valid tree); for `n = 1` with no edges, the result is also `True`.
- If `n > 0` and the number of edges is not exactly `n - 1`, the answer is immediately `False`.
- When `n > 0` and the edge count equals `n - 1`, a single DFS or BFS from any node is sufficient: if it visits all `n` nodes without revisiting a parent, the graph is a tree; otherwise it either contains a cycle or is disconnected.
- Edges are undirected, so each edge `[u, v]` connects both `u` to `v` and `v` to `u`.
