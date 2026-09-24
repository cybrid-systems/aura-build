# Binary Tree Cameras

## Problem

You are given the root of a binary tree with `n` nodes, numbered `0` to `n-1` (the values on the nodes are irrelevant). Each node may have at most two children, identified by their node indices; `-1` denotes "no child".

A camera placed on a node monitors that node itself, its parent, and both of its children. Your task is to choose a minimum-size set of nodes on which to install cameras so that **every** node in the tree is monitored by at least one camera.

Return that minimum number.

## Function Signature

```
def solve(parent: list[int], left: list[int], right: list[int]) -> int:
```

- `parent[i]` — index of the parent of node `i`, or `-1` for the root.
- `left[i]`, `right[i]` — indices of the left and right children of node `i`, or `-1`.
- The arrays each have length `n`, with `1 ≤ n ≤ 1000`.

## Input / Output (CASE0 convention)

The harness feeds parameters positionally:

```
CASE0=parent=[4,-1,4,0,1] left=[1,3,-1,-1,-1] right=[2,-1,-1,-1,-1]
```

Your `solve` function must return the answer as an integer. For the example above, the minimum number of cameras is `1` (placing it on the root monitors the entire tree).

## Notes

- The tree is guaranteed to be valid: exactly one node has `parent == -1` (the root), and the child/parent relations are consistent.
- You may return the cameras in any layout; only the **count** matters.
- Think in terms of three states per node: *needs monitoring*, *has a camera*, and *already covered*. A classic post-order DFS with a greedy choice ("place a camera only when a child needs monitoring") yields the optimal count.
