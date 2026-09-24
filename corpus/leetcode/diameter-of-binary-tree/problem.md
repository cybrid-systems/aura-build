# Diameter of Binary Tree

## Problem

Given the root of a binary tree, return the **diameter** of the tree.

The diameter is defined as the **length of the longest path between any two nodes** in the tree. This path may or may not pass through the root, and its length is measured by the **number of edges** along the path.

A tree with a single node has a diameter of `0`.

## Function Signature

```
(solve [root] -> int)
```

- `root` is a binary-tree node value containing fields `val`, `left`, and `right`. A null node is represented by the special symbol `None`.

## Input / Output Convention

The harness reads a single CASE0 line of the form:

```
CASE0=(root representation)
```

For example:

```
CASE0=(1 (2 (4 None None) (5 None None)) (3 None None))
```

This represents the tree:

```
        1
       / \
      2   3
     / \
    4   5
```

Your implementation must return an integer equal to the diameter (in edges). For the tree above, the longest path is `4 → 2 → 1 → 3` (or `5 → 2 → 1 → 3`), which contains **3 edges**, so the answer is `3`.

## Notes

- A node with no children has a diameter of `0`.
- If a node has exactly one child, the diameter may still be non-zero if a deeper subtree exists on the other side via the path through the root of that subtree.
- You may find it convenient to compute, for each node, the longest downward path (in edges) from that node to a leaf, then update a global maximum with the sum of the two best downward paths through that node.
