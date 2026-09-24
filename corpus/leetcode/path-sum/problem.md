# Path Sum

## Problem

Given the `root` of a binary tree and an integer `targetSum`, determine whether the tree contains a **root-to-leaf path** whose node values sum to exactly `targetSum`.

A *root-to-leaf path* is a path that starts at `root` and ends at any leaf node (a node with both `left` and `right` set to `nil`). The nodes along the path contribute their `Val` to the running sum.

Return `true` if such a path exists, otherwise `false`.

## Function Signature

```go
func solve(root *TreeNode, targetSum int) bool
```

## Input / Output Convention

The harness drives the solution line-by-line through an `Aura`-style protocol on stdin-less mode. Each case is supplied as a series of lines:

```
CASE0=-10 9 20 null null 15 7,sum=22
CASE0_ANS=true
CASE1=1 2 3,sum=5
CASE1_ANS=false
CASE2=,sum=0
CASE2_ANS=false
```

- The first comma-separated token list encodes the tree in **level-order** (BFS) traversal; `null` (or an empty segment) marks a missing child.
- `sum=K` is the target sum (`K` may be negative or zero).
- `CASE_n_ANS` is the expected boolean answer: `true` or `false`.

The solver reads each `CASE`, reconstructs the tree, calls `solve(root, targetSum)`, and compares its return value with the declared answer.

## Notes

- An **empty tree** (no nodes) has no root-to-leaf path, so `solve(nil, targetSum)` is always `false`, even when `targetSum == 0`.
- Path equality only counts when the sum is reached **exactly at a leaf**. Do not stop early at internal nodes.
- Values are not bounded: node values and `targetSum` may be any 32-bit signed integer.
- Expected complexity: **O(n)** time, **O(h)** auxiliary space (where `h` is the tree height) for a single traversal.
