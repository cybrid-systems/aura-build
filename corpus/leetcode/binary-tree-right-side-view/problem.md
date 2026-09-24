# Binary Tree Right Side View

## Problem

Given the root of a binary tree, imagine standing on the **right side** of the tree. Return the list of node values that are visible from this viewpoint, ordered from **top to bottom**.

A node is visible from the right side if no other node lies strictly to its right at the same depth. For each depth, only the rightmost node (the last one encountered when scanning that level left-to-right) contributes its value to the answer.

You must compute the answer using a **Breadth-First Search (BFS)** traversal — i.e., process the tree level by level using a queue.

## Function Signature

```python
def solve(root) -> list[int]:
    ...
```

The input `root` is the root node of a binary tree (or `None` for an empty tree). Each node has integer attributes `.val`, `.left`, and `.right`.

## Input / Output Convention

There is **no stdin**. The Aura harness invokes `solve(root)` directly. To make examples reproducible on the harness, the same inputs are mirrored as `CASE0=...` lines below — these are comments for reference only and are **not** read by the solution.

```
CASE0 root = [1,2,3,null,5,null,4]
CASE1 root = [1,2,3,4,null,null,null,5]
CASE2 root = [1,null,3]
CASE3 root = []
```

Expected outputs:

```
CASE0 -> [1, 3, 4]
CASE1 -> [1, 3, 4, 5]
CASE2 -> [1, 3]
CASE3 -> []
```

## Notes

- The tree may have up to ~10^4 nodes; an O(n) BFS is expected.
- An empty tree must return `[]`, not `None`.
- Levels with only one node still contribute that node's value (it is trivially both leftmost and rightmost).
