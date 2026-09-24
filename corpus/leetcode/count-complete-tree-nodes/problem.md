# Count Complete Tree Nodes

Given the `root` of a **complete** binary tree, return the number of nodes in the tree.

A complete binary tree is one in which every level, except possibly the last, is completely filled, and all nodes in the last level are as far left as possible.

Your solution must run in better than `O(n)` time (i.e., sub-linear in the number of nodes for typical complete trees).

## Function Signature

```python
def solve(root) -> int:
    ...
```

## Input / Output Convention

The driver feeds a tree encoded as a level-order array. The first line is the case label, the second line is the array:

```
CASE0=count-complete-tree-nodes
[1, 2, 3, 4, 5, 6]
```

A node value of `None` (rendered as the string `null`) represents an absent child. The `root` argument is a binary tree node class with fields `val`, `left`, and `right`. Empty input (`[]`) represents an empty tree and should return `0`.

## Notes

- A purely `O(n)` traversal will not be accepted; you must exploit the complete-tree property.
- Hint: compare the leftmost and rightmost depths from `root`. If they are equal, the tree is a full binary tree with `2^d - 1` nodes and you can skip walking it.
