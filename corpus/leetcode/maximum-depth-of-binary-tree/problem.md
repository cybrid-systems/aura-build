# Maximum Depth of Binary Tree

## Problem

Given the root of a binary tree, find the number of nodes along the longest path from the root down to the farthest leaf.

A leaf is a node with no children. The path length is counted as the number of nodes visited (including both the root and the leaf).

## Function Signature

```clojure
(solve root)
```

`root` is a tree node value with the following structure:

- An atom (non-nil atom) representing a node, where dereferencing it yields a map with two keys:
  - `:left` — the left child node, or `nil` if absent
  - `:right` — the right child node, or `nil` if absent

The input `root` itself is an atom (the root node). If `root` is `nil`, the tree is empty and the depth is `0`.

## Input

The input is provided as a single line in the following format:

```
CASE0=<atom-printed-form>
```

For example, `CASE0=ATOM0` where `ATOM0` is bound to the root of the tree. The atom-printed form is just the printed name of the root atom; you may dereference it to walk the tree.

## Output

Print a single integer: the number of nodes on the longest root-to-leaf path.

## Notes

- An empty tree (`root` is `nil`) has depth `0`.
- A tree consisting of a single node has depth `1`.
- The depth equals `1 + max(depth(left), depth(right))`, where the depth of a `nil` subtree is `0`.
