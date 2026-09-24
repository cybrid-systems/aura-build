# Invert Binary Tree

Given the `root` of a binary tree, invert the tree and return its root. Inverting means swapping the left and right child of every node in the tree (a mirror reflection along the vertical axis).

The tree contains nodes with an integer value and `left` / `right` child pointers. Input nodes may carry any integer (including negatives); only the tree's shape and pointers matter for this problem.

## Function Signature

```clojure
(solve root)
```

- `root`: the root node of a binary tree, or `nil` if the tree is empty. Each node exposes `val`, `left`, and `right`.

**Return**: the root of the inverted tree. The input tree may be mutated, or a new tree may be returned — either is accepted as long as the resulting structure is the mirror of the original.

## Input Convention (CASE0 lines)

The harness feeds each test case as a single line beginning with `CASE0=` followed by a level-order serialization of the binary tree using `nil` for missing children, e.g.

```
CASE0=(root (1 (2 (4 nil nil) (5 nil nil)) (3 (6 nil nil) nil)))
```

or, for a flat level-order form,

```
CASE0=[4,2,7,1,3,6,9]
```

`nil` represents an absent child. Empty input (`CASE0=nil` or `CASE0=` empty) means an empty tree.

## Notes

- An empty tree (`nil`) inverts to itself (`nil`).
- The result must be the exact mirror image: for every node, its `left` becomes its `right` and vice versa, recursively for all descendants.
- Both recursive and iterative approaches are viable; the structure of the tree is what matters, not the values stored in the nodes.
