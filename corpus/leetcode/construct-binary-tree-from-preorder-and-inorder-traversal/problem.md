# Construct Binary Tree from Preorder and Inorder Traversal

## Problem

You are given two arrays that describe the same binary tree (nodes with distinct integer values):

- **preorder**: the tree's nodes in preorder traversal (Root, Left, Right)
- **inorder**: the tree's nodes in inorder traversal (Left, Root, Right)

Reconstruct the original binary tree and return its **postorder** traversal (Left, Right, Root).

It is guaranteed that a unique binary tree corresponds to the given traversals.

## Function Signature

```
def solve(preorder: list[int], inorder: list[int]) -> list[int]:
    ...
```

## Input / Output Convention

The harness feeds the function via two case lines on stdin:

```
CASE0_PRE=4,2,1,3,6,5,7
CASE0_INORDER=1,2,3,4,5,6,7
```

`CASE0_PRE` and `CASE0_INORDER` define the two traversal arrays for case 0. Your function must return a `list[int]` representing the postorder traversal of the reconstructed tree.

For the example above, the expected postorder is `1,3,2,5,7,6,4`.

## Notes

- The tree may be skewed; recursion depth can reach `len(preorder)`. Consider iterative or index-based approaches if recursion limits matter.
- Values are distinct integers; no duplicates to disambiguate.
