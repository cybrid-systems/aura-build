# Balanced Binary Tree

## Problem

You are given the root of a binary tree. A binary tree is **height-balanced** if, for every node in the tree, the absolute difference between the depths of its left and right subtrees is at most `1`. An empty tree (no nodes) is considered balanced. A single-node tree is also considered balanced.

Determine whether the given tree is height-balanced and return an appropriate boolean indicator.

## Function Signature

```clojure
(defn solve [root] ...)
```

- `root` is the root node of a binary tree. Each node is represented as a map `{:val v :left l :right r}` where `v` is an integer value and `l` / `r` are child nodes or `nil`. The root may itself be `nil`.
- Return `true` if the tree is height-balanced, otherwise `false`.

## Input / Output (Harness Convention)

The harness constructs the tree internally. You only need to implement `solve`.

For reference, the on-disk layout that feeds the harness looks like:

```
CASE0=expected=true
TREE0_NODES=5
TREE0_ROOT=0
TREE0_NODE_0_VAL=1
TREE0_NODE_0_LEFT=1
TREE0_NODE_0_RIGHT=2
TREE0_NODE_1_VAL=2
TREE0_NODE_1_LEFT=-1
TREE0_NODE_1_RIGHT=-1
TREE0_NODE_2_VAL=3
TREE0_NODE_2_LEFT=3
TREE0_NODE_2_RIGHT=4
TREE0_NODE_3_VAL=4
TREE0_NODE_3_LEFT=-1
TREE0_NODE_3_RIGHT=-1
TREE0_NODE_4_VAL=5
TREE0_NODE_4_LEFT=-1
TREE0_NODE_4_RIGHT=-1
CASE1=expected=false
...
```

- `CASEk=expected=<true|false>` declares the expected answer for case `k`.
- `TREEn_NODES` gives the number of nodes in the tree (nodes are numbered `0..N-1`, where node `0` is the root by convention unless overridden by `TREEn_ROOT`).
- `TREEn_NODE_i_VAL` is the value stored at node `i`.
- `TREEn_NODE_i_LEFT` / `TREEn_NODE_i_RIGHT` are the indices of the left/right children, or `-1` if the child is absent.
- `TREEn_ROOT` (optional) overrides the root index; if omitted, node `0` is the root.

## Notes

- A tree with a single node is balanced. An empty tree (`nil` root) is balanced.
- The empty child marker `-1` denotes `nil`, not a node with value `-1`.
- The solution must check the balance condition at every node, not just at the root. A common pitfall is to compare only the heights of the root's two subtrees and miss deeper violations.
