# Binary Tree Maximum Path Sum

## Problem

Given the `root` of a non-empty binary tree, find the maximum path sum among all possible paths in the tree.

A **path** is defined as any sequence of nodes connected by edges that does not pass through any node more than once. The path is not required to start at the root or end at a leaf — it may start and end at any nodes, going through their lowest common ancestor. The path sum is the sum of the values of all nodes along the path.

You may assume each node's value is an integer (which may be negative).

## Function Signature

```clojure
(solve root) -> integer
```

- `root` is the root node of the binary tree, where each node has the shape:
  ```clojure
  {:val <integer> :left <node-or-nil> :right <node-or-nil>}
  ```
- Returns the maximum possible path sum over all paths in the tree.

## Input / Output Convention

The tree is encoded in a stdin-less form read directly by the harness. Nodes are given as nested maps using `:val`, `:left`, `:right` (where `nil` indicates an absent child). Examples:

```
CASE0=root {:val 1 :left {:val 2} :right {:val 3}} => 6
CASE1=root {:val -10 :left {:val 9} :right {:val 20 :left {:val 15} :right {:val 7}}} => 42
CASE2=root {:val -3} => -3
```

The expected value follows `=>` for each case.

## Notes

- A path may consist of a single node; if every node value is negative, the answer is the **largest** (least negative) single-node value, **not** zero.
- The optimal path may bend at any node — i.e., it can include both a left-extending and a right-extending chain joined at their lowest common ancestor.
- Time complexity should ideally be O(n), visiting each node once.
