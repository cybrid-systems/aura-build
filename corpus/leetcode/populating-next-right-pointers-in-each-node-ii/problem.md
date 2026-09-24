# Populating Next Right Pointers in Each Node II

## Problem Statement

Given a binary tree where each node has an integer value, a `left` child pointer, and a `right` child pointer, populate each node's `next` pointer so that it points to the next right node at the same level. Nodes at the rightmost position of each level should have `next` set to `null` (the default).

Unlike the variant where the tree is guaranteed to be a **perfect** binary tree, here the input may be **any** binary tree — levels can be incomplete, and individual nodes may have only a left child, only a right child, or no children at all.

Your task is to connect all `next` pointers correctly for every level of the tree, then return the root.

### Function to Implement

```lisp
(defun solve (root)
  ;; root is a tree node with fields: val, left, right, next
  ;; mutate each node's `next` field to point to the next right node
  ;; at the same level, or NIL if there is none.
  ;; Return the root node.
  )
```

## Input / Output Convention

The harness reads a single test case from standard input. Node fields are space-separated on each line. The first line is the root of the tree in level-order (`BFS`/breadth-first) using the encoding:

- `-1` represents a `null` child.
- Any other integer is a node value.
- A node at position `i` has its left child encoded at position `2*i + 1` and its right child at position `2*i + 2`, where `i` is the index in a flattened level-order list starting from the root.

### Format

```
CASE0=1 2 3 4 5 -1 7
```

The line begins with the prefix `CASE0=` followed by the level-order encoding of the tree. A sentinel `-1` terminates the list (any further values are ignored).

### Expected Output

Print the resulting tree in the same level-order encoding, with each node's `val` followed by its `next` pointer (or `0` to indicate `null`), again space-separated on one line, prefixed by `CASE0=`.

```
CASE0=1 0 2 3 4 5 7 0 0 0 0 0 0 0 0
```

The output length depends on the number of nodes reachable through `left`/`right` pointers from the root after the traversal.

## Notes

- The `next` field of every node must be set, including the rightmost node of each level (which should be `0` / `null`).
- Because the tree is not necessarily perfect, a simple recursive "perfect tree" solution will not work — you must handle arbitrary shapes.
- The algorithm should run in `O(n)` time and `O(1)` auxiliary space (excluding recursion stack) for full credit. A common approach is to use the existing `next` pointers of the previous level to traverse the current level.
