# Binary Tree Paths

## Problem

Given the root of a binary tree, return every path from the root to a leaf node. Each path should be formatted as a string of the node's integer values (in order from root to leaf) joined together by the arrow `->` separator.

A leaf is a node with no children.

If the tree is empty (root is `null`), return an empty list.

## Function Signature

```clojure
(defn solve [root] ...)
```

- `root` is the root node of a binary tree. Each node has the shape `{:val v :left l :right r}` where `v` is an integer, and `l`/`r` are either child nodes with the same shape or `nil`.

## Input Convention

The harness reads cases from a single line. For each case the tree is provided in `CASE0=` format using a level-order serialization:

- `null` represents an absent node.
- Nodes are comma-separated in breadth-first order.

For example:

```
CASE0=[1,2,3,null,5]
CASE0=[1]
CASE0=[]
```

- For `CASE0=[1,2,3,null,5]` the tree is:
  ```
          1
         / \
        2   3
         \
          5
      ```
  Expected paths: `["1->2->5", "1->3"]`

- For `CASE0=[1]` the tree is a single leaf node. Expected paths: `["1"]`.

- For `CASE0=[]` (empty input) the tree is empty. Expected paths: `[]`.

## Output Convention

For each input case, the solver should produce a single line with the list of paths formatted as a Clojure vector of strings, for example:

```
["1->2->5" "1->3"]
["1"]
[]
```

## Notes

- The relative order of paths in the output is not significant for judging purposes; the harness will compare results as a multiset of strings.
- Only `->` (hyphen followed by greater-than) is used as the separator.
- Both left and right subtrees of any non-leaf must be traversed; the function should not stop early at nodes that have one missing child.
