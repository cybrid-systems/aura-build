# Path Sum III

## Problem

Given the root of a binary tree and an integer `target`, count the number of paths whose node values sum to `target`.

A path is defined as a sequence of nodes connected by edges that goes **downward** — from some ancestor node down to any descendant node. In particular:

- The path may start at any node (not necessarily the root).
- The path may end at any node (not necessarily a leaf).
- Nodes along a path must follow parent-to-child edges (no upward movement).
- The path must contain at least one node.

Return the total number of such paths.

## Function Signature

```python
def solve(root: TreeNode, target: int) -> int:
    ...
```

## Input / Output Convention (Aura harness)

The harness reads a single CASE line from the problem description and feeds the parsed values to `solve`. No stdin is used.

For this problem the CASE line has the form:

```
CASE0=root=[10,5,-3,3,2,null,11,3,-2,null,1], target=8
```

- `root` is a binary tree serialized in level-order using `null` for missing children. The list is a flat array; for each index `i`, its left child is at `2*i+1` and right child at `2*i+2` (within the range of the list).
- `target` is an integer.

`solve` receives the constructed `TreeNode` root (or `None` if the list is empty) and the integer `target`, and must return the count of valid paths.

## Notes

- An empty tree (root is `None`) has no paths, so the answer is `0`.
- Different paths that share some nodes but differ in their starting or ending node count as distinct paths.
- Tree node values fit in standard 32-bit signed integers; however, intermediate prefix sums can be negative, so do not assume non-negative values.
