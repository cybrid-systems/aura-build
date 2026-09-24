# Kth Smallest Element in a BST

## Problem

Given the root of a binary search tree (BST) and an integer `k`, return the **k-th smallest** value (1-indexed) among all the node values in the tree.

You may assume that `k` is always valid: `1 ≤ k ≤ number of nodes in the tree`.

The BST property guarantees that an in-order traversal yields the node values in **sorted (ascending)** order, which is the key to an efficient solution.

## Function Signature

```python
def solve(root, k):
    ...
```

- `root`: the root node of the BST (each node has `val`, `left`, `right` attributes). May be `None`.
- `k`: integer, 1-indexed position in the sorted order.

**Returns**: the value of the k-th smallest node.

## Input / Output Convention

The harness feeds the function directly; no stdin is read. For reference, the underlying case format is:

```
CASE0_ROOT=[2,1,3]
CASE0_K=1
CASE1_ROOT=[5,3,6,2,4,null,null,1]
CASE1_K=3
```

Each `CASE<n>_ROOT` is a level-order representation of the BST (`null` for missing children). The function is called once per case with the decoded arguments.

### Examples

| Input (root, k)          | Output |
|--------------------------|--------|
| `[2,1,3]`, k=1           | `1`    |
| `[5,3,6,2,4,null,null,1]`, k=3 | `3` |
| `[5,3,6,2,4,null,null,1]`, k=6 | `6` |

## Notes

- **Expected complexity**: `O(h + k)` time, where `h` is the tree height, by descending the tree and counting nodes visited rather than traversing the whole tree. `O(h)` space (recursion stack).
- A full in-order traversal followed by indexing is correct but not optimal for large trees with small `k`; the idiomatic solution stops as soon as the k-th node is found.
- Make sure to handle `root is None` gracefully (return `None` or raise — match the harness's expectation, here we return `None`).
