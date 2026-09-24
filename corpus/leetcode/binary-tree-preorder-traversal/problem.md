# Binary Tree Preorder Traversal

## Problem Statement

Given the root of a binary tree, return the values of its nodes in **preorder** traversal order (visit the current node, then recursively traverse the left subtree, then the right subtree).

You may implement the traversal either recursively or iteratively. The input tree is represented as a flat, level-order list where `null` marks the absence of a child (a common convention used by LeetCode-style problems). The list contains at least the root node.

Your task is to produce the preorder sequence of node values.

## Function Signature

```lisp
(defun solve (root)
  ;; root: a vector (or list) of level-order node values,
  ;;       with NIL representing null/missing nodes.
  ;; returns: a list of node values in preorder.
  )
```

## Input / Output Convention

The harness invokes `solve` with a single argument `root`, which is a Common Lisp vector containing the level-order representation of the tree, e.g. `#(1 2 3 NIL 5 NIL 4)` for:

```
        1
       / \
      2   3
       \   \
        5   4
```

The function must return a flat list (e.g. `(1 2 5 3 4)`) of the node values visited in preorder.

## Examples

**Example 1**
- Input root: `#(1 NIL 2 NIL 3)`
- Tree:
  ```
      1
       \
        2
         \
          3
  ```
- Expected output: `(1 2 3)`

**Example 2**
- Input root: `#(1 2 3 4 5 6 7)`
- Tree: a complete binary tree with values 1..7.
- Expected output: `(1 2 4 5 3 6 7)`

## Notes

- `NIL` entries in the input vector denote missing children; you may rely on the convention that children of node at index `i` are at indices `2*i + 1` and `2*i + 2` (0-indexed).
- Only the non-null nodes should appear in the output, in the order defined by preorder traversal.
- The tree contains at least one node; you do not need to handle empty-input edge cases beyond that.
