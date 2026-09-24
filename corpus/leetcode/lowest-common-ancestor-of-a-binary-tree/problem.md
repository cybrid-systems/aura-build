# Lowest Common Ancestor of a Binary Tree

## Problem

Given the root of a binary tree and references to two distinct nodes `p` and `q` already present in the tree, find and return the **Lowest Common Ancestor (LCA)** of the two nodes.

The LCA of two nodes `x` and `y` in a tree is defined as the lowest node that has both `x` and `y` as descendants (a node is allowed to be a descendant of itself).

The tree nodes are generic — they are **not** guaranteed to be a Binary Search Tree, so values alone cannot be used to guide the search. You must rely purely on the tree structure.

## Function Signature

```clojure
(solve root p q) ; -> node
```

- `root`: the root node of the binary tree (may be `nil`).
- `p`, `q`: references to two distinct nodes in the tree (each is a node object, not a value).
- Returns the node object that is the LCA of `p` and `q`.

Assume the node type exposes at least:
- `val`   — the node's value (any comparable value)
- `left`  — left child or `nil`
- `right` — right child or `nil`

## I/O Convention (stdin-less Aura harness)

The harness injects the test cases directly. When running locally for debugging, the input format is:

```
CASE0=root=[3,9,20,null,null,15,7]; p=9; q=20; expect=3
CASE1=root=[1,2,3,4,5,null,6]; p=4; q=5; expect=2
CASE2=root=[1,2]; p=1; q=2; expect=1
CASE3=root=[1]; p=1; q=1; expect=1
```

For each `CASE` line, the solver must return the node that is the LCA; the harness compares its identity (or value, if no node references are available) against `expect`.

## Notes

- `p` and `q` are guaranteed to be distinct nodes, except in edge cases where the tree has a single node — handle that case explicitly.
- A node can be its own descendant, so if `p` is an ancestor of `q` (or vice-versa), the answer is that ancestor node itself.
- Aim for a single recursive traversal of the tree (O(n) time, O(h) space for the recursion stack, where `h` is tree height).
- `root`, `p`, or `q` may be `nil` only in pathological inputs; the problem statement guarantees both `p` and `q` exist in the tree when `root` is non-nil.
