# Populating Next Right Pointers in Each Node

## Problem

Given a **perfect binary tree** where every internal node has two children (left and right), populate each node's `next` pointer so that it points to its immediate neighbor on the same level. Nodes at the rightmost position of each level should have `next` set to `None` (or `null`).

Each node in the tree has the following structure:

```
class Node:
    def __init__(self, val: int,
                 left: 'Node' = None,
                 right: 'Node' = None,
                 next: 'Node' = None):
        self.val = val
        self.left = left
        self.right = right
        self.next = next
```

You must connect all `next` pointers **without using any extra space** for a level-by-level traversal (i.e., only the implicit call stack or queue already used by recursion/iteration is allowed for storage).

## Function Signature

```python
def solve(root: Node) -> Node:
    ...
```

`root` is the root node of the perfect binary tree. Return the root after all `next` pointers have been populated.

## Input / Output Convention

The harness drives the solution through standard input. Each case uses the following two-line format:

```
CASE0=...   # size of tree (number of nodes, a positive integer)
CASE1=...   # level-order traversal of the tree; use "N" for a missing child (not used here since the tree is perfect)
```

For example, a perfect binary tree of 7 nodes `[1,2,3,4,5,6,7]` looks like:

```
CASE0=7
CASE1=1 2 3 4 5 6 7
```

After processing, the returned tree must have its `next` pointers filled so that, walking each level left-to-right and following `next`, the traversal reads the nodes in order; the rightmost node's `next` is `None`.

## Notes

- The tree is guaranteed to be perfect, so you do not have to handle missing children.
- Aim for an **O(n)** time solution where each node is visited a constant number of times.
- Constant extra space (i.e., not growing with `n`) is expected — using the already-existing `next` pointers themselves to traverse levels is the classic trick here.
