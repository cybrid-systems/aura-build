# Clone Graph

## Problem

You are given a reference to a single node `u` in a **connected undirected graph**. Each node has the following structure:

```python
class Node:
    def __init__(self, val=0, neighbors=None):
        self.val = val
        self.neighbors = neighbors if neighbors is not None else []
```

- Every node's value is unique and lies in the range `[1, 100]`.
- The number of nodes in the graph is at most `100`.
- The graph is connected (every node is reachable from `u`).

Your task is to return a **deep copy** of the entire graph: a brand-new set of `Node` objects whose structure (nodes and adjacency relationships) exactly mirrors the original, but which share no references with the input graph.

## Function Signature

```python
def solve(start: Node) -> Node:
    ...
```

`start` is a reference to any node in the original graph (commonly the entry node). Return a reference to the corresponding cloned node in the deep copy.

## Input / Output Convention

The harness loads the graph before calling `solve`. The starting node reference is passed as the `start` argument. There is no `CASE0=` style line — your `solve` function simply receives the live node.

For debugging in a local driver you may assume an equivalent line such as:

```
CASE0=Node(1)
# graph is constructed in-memory before solve() is invoked
```

## Notes

- Returning the input node itself is **not** a valid deep copy — every node must be freshly allocated.
- Use a hash map (original node → cloned node) to avoid re-creating a node or falling into infinite recursion when revisiting neighbors.
- Both BFS and DFS are acceptable traversal strategies.
