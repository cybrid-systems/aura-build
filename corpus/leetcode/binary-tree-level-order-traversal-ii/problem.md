# Binary Tree Level Order Traversal II

## Statement

Given the root of a binary tree, return the values of its nodes grouped by level, but **from the bottom level up to the root**. Each inner list contains the values of all nodes at the same depth, visited left-to-right.

If the tree is empty, return an empty result.

## Function Signature

```clojure
(solve root)
```

- `root` — the root node of a binary tree (or `nil` for an empty tree). Each node has integer fields `val`, `left`, and `right`.

The function should return a vector of vectors, where each inner vector represents one level of the tree, ordered from the deepest level up to the root level.

## Input / Output Convention (Aura harness)

The tree is encoded directly as nested S-expression-style lists using the symbols `node` and `nil`:

- `nil` represents an empty tree or a missing child.
- `(node VAL LEFT RIGHT)` represents a node with value `VAL` and children `LEFT` and `RIGHT`.

A single line is provided on standard input:

```
CASE0=(node 3 (node 9 nil nil) (node 20 (node 15 nil nil) (node 7 nil nil)))
```

Your solution should read this line, parse the tree, and output the bottom-up level order traversal as a single line:

```
[[15 7] [9 20] [3]]
```

For an empty tree (`CASE0=nil`), output an empty list: `[]`.

## Notes

- Output must be a single line. Use the same compact bracket-style format shown above for vectors.
- A pure BFS from the root (queue per level) followed by reversing the collected levels is a natural approach, but a DFS with depth tracking that prepends each new level also works.
- Levels themselves must remain left-to-right; only the order *between* levels is reversed.
- Assume node values fit comfortably in a standard signed integer range, but the tree may have any depth that the host language can handle recursively (or use an iterative stack if recursion depth is a concern).
