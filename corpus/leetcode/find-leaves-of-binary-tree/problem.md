# Find Leaves of Binary Tree

## Problem

Given the root of a binary tree, collect the values of its leaf nodes **level by level**.

A leaf is a node with no children. To produce each level:

1. Identify every leaf in the current tree.
2. Record their values (in any order per level — the official convention is left-to-right).
3. Remove those leaves from the tree.
4. Repeat on the now-smaller tree until no nodes remain.

Return the collected levels as a list of lists of integers.

## Function Signature

```text
def solve(root: TreeNode) -> List[List[int]]:
    ...
```

A `TreeNode` has integer `val`, `left`, and `right` attributes. `root` may be `None`, in which case return `[]`.

## Input / Output Convention

The harness does not use stdin. Instead, the solution is invoked directly via the `solve` function.

For local debugging and reference, the equivalent textual I/O form is:

```
CASE0=[] 
CASE0OUT=[]
CASE1=[1,2,3]
CASE1OUT=[[2,3],[1]]
CASE2=[1,2,3,4,5]
CASE2OUT=[[4,5,3],[2],[1]]
```

Here each `CASEn` is the level-order traversal of the tree (using `null` for missing children), and `CASE_n_OUT` is the expected return value.

## Notes

- The order of values **within** each level is not significant; only the set of levels matters. The reference harness uses left-to-right order.
- An empty tree yields an empty list `[]`, not a list containing an empty list.
- A tree with a single node has one level: `[[v]]`.
- Aim for an efficient solution; repeatedly scanning for leaves is acceptable, but a single bottom-up height computation yields the same levels in `O(n)` time.
