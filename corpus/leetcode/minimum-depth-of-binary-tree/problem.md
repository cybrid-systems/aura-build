# Minimum Depth of Binary Tree

Given the `root` of a binary tree, find the **minimum depth** of the tree.

The minimum depth is defined as the number of nodes along the **shortest path** from the root down to the **nearest leaf** node. A leaf is a node that has no children.

Note that an empty tree (no root) has depth `0`. Also, when only one child of a node exists, the path must go through that child — you cannot skip a level, so nodes with a single child are themselves *not* considered leaves for this problem.

## Function Signature

```python
def solve(root) -> int:
    ...
```

Where `root` is a binary tree node (with `.val`, `.left`, `.right` attributes) or `None`.

## Input / Output Convention

The harness exercises your `solve` function directly. The following lines describe a sample run for verification:

```
CASE0_ROOT = [3, 9, 20, null, null, 15, 7]
CASE0_ANSWER = 2
```

- `CASE0_ROOT` is the level-order representation of the binary tree (using `null` for absent children), as commonly serialized by LeetCode-style problems.
- `CASE0_ANSWER` is the expected output for that case.

## Notes

- Example: the tree `[3, 9, 20, null, null, 15, 7]` has minimum depth `2` (the path `3 → 9`), even though its maximum depth is `3`.
- Empty input → output `0`.
- Be careful with single-child subtrees: a node with only one child is **not** a leaf, and the depth must reflect going through that one existing child.
- Solutions based on BFS naturally stop at the first encountered leaf; DFS / recursion work as well.
