# Lowest Common Ancestor of a Binary Search Tree

## Problem

Given the root of a **Binary Search Tree** (BST) and two node references `p` and `q`, return the **Lowest Common Ancestor (LCA)** of the two nodes.

The LCA of two nodes `p` and `q` in a BST is defined as the lowest node `T` such that `T` is an ancestor of both `p` and `q` (a node can be an ancestor of itself).

You may assume that both `p` and `q` exist as distinct nodes in the tree.

### BST property reminder
For every node `x`:
- All keys in the left subtree of `x` are strictly less than `x.val`.
- All keys in the right subtree of `x` are strictly greater than `x.val`.

## Function Signature

```python
def solve(root, p, q):
    """
    :param root: TreeNode — root of the BST
    :param p: TreeNode — first target node
    :param q: TreeNode — second target node
    :return: TreeNode — the lowest common ancestor of p and q
    """
```

## Input / Output Convention (Aura harness)

The harness supplies a single case on stdin in the following form. No manual parsing is required; values are already converted into the function arguments.

```
CASE0_ROOT=[2,1,3]
CASE0_P=1
CASE0_Q=3
CASE0_EXPECTED=2
```

- `CASE0_ROOT` is a **level-order** array representation of the BST. `null` denotes a missing child.
- `CASE0_P`, `CASE0_Q` are the node **values** (not references). The harness reconstructs the tree, locates the nodes with these values, and passes them as `TreeNode` objects to `solve`.
- `CASE0_EXPECTED` is the value of the node that `solve` must return (its `val`).

Additional cases (`CASE1_…`, `CASE2_…`, …) follow the same pattern.

## Examples

**Example 1**
```
CASE0_ROOT=[6,2,8,0,4,7,9,null,null,3,5]
CASE0_P=2
CASE0_Q=8
CASE0_EXPECTED=6
```

**Example 2**
```
CASE0_ROOT=[6,2,8,0,4,7,9,null,null,3,5]
CASE0_P=2
CASE0_Q=4
CASE0_EXPECTED=2
```

## Notes

- Leverage the BST ordering property to solve in `O(h)` time, where `h` is the height of the tree (worst case `O(n)`, best case `O(log n)`). A generic binary-tree LCA approach (`O(n)`) also works but is not optimal.
- A node is a valid ancestor of itself, so if one target equals the root, the root is the LCA.
