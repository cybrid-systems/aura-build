# House Robber III

## Problem

The thief has discovered a new area for robbing. Each house is arranged in a binary tree (rooted at node 0). Each node represents a house with a non-negative amount of money, and each edge connects two directly adjacent houses. Robbing two directly-linked houses in one night will alert the police.

Given the root of the binary tree, return the maximum amount of money the thief can rob in one night without robbing two adjacent (parent-child) houses.

`n` is the number of nodes; `0 ≤ n ≤ 10^4`.

## Function Signature

```lisp
(solve TREE) -> integer
```

`TREE` is a flat list describing the tree (see I/O below). Return the maximum money that can be robbed.

## Input

A single test case is read from standard input. Lines that start with `CASE0=` provide the test data for this problem; ignore any later `CASEn=` lines.

The value after `CASE0=` is a flat representation of the binary tree in level-order (breadth-first), where missing children are encoded as `-1` (or any negative sentinel). The i-th number corresponds to the i-th node in level order; a non-negative number is the money at that node.

For example, the tree

```
      3
     / \
    2   3
     \   \
      3   1
```

is encoded as `3 2 3 -1 -1 -1 1`.

The tree is guaranteed to be well-formed under this encoding. The list length is in `[0, 10^5]` and each value fits in a 32-bit signed integer.

## Output

A single line containing the maximum amount of money that can be robbed.

## Notes

- A leaf node may always be robbed.
- An empty tree (`TREE` empty, or root encoded as `-1`) yields answer `0`.
- A standard approach returns, for each subtree, the pair `(rob_this, skip_this)` — the best when the current node is robbed versus skipped — and combines them bottom-up.
