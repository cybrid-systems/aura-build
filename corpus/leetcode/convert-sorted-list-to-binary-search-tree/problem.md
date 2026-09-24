# Convert Sorted List to Binary Search Tree

## Statement

Given the head of a singly linked list whose node values are sorted in strictly ascending order, return the root of a **height-balanced** binary search tree (BST) whose node values come from the list. The BST must satisfy:

- Every left subtree contains only nodes with keys less than the node's key.
- Every right subtree contains only nodes with keys greater than the node's key.
- For every node, the heights of its left and right subtrees differ by at most one.

A list node and a tree node are defined as:

```
class ListNode:
    val: int
    next: ListNode | None

class TreeNode:
    val: int
    left: TreeNode | None
    right: TreeNode | None
```

## Function Signature

```
def solve(head: ListNode | None) -> TreeNode | None:
    ...
```

## Input / Output Convention (Aura Harness)

The harness calls `solve(head)` directly. The input list is encoded as `CASE0=` lines before the call:

```
CASE0=length
CASE0_VALS=v1 v2 v3 ... vN
```

`length` is the number of nodes. `v1 v2 ... vN` are the node values in list order (ascending). After the `CASE0` block, the call is executed; the function returns the root of the constructed balanced BST.

For example, the list `-10 -> -3 -> 0 -> 5 -> 9` is encoded as:

```
CASE0=5
CASE0_VALS=-10 -3 0 5 9
```

and `solve(head)` should return the root of a height-balanced BST containing those five values.

## Notes

- The list length may be zero (`CASE0=0`, no `CASE0_VALS` line). In that case, return `None`.
- A height-balanced tree on `N` nodes has height `⌊log₂ N⌋` or `⌊log₂ N⌋ + 1`.
- Any balanced BST that contains exactly the given values is acceptable, but the canonical solution picks the middle element as the root recursively.
