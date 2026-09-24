# Unique Binary Search Trees II

## Problem

Given an integer `n`, generate **all structurally unique Binary Search Trees (BSTs)** that store the values `1` through `n`.

Each node of a BST must satisfy:

- The value of every node in the left subtree of a node is **strictly less** than the node's value.
- The value of every node in the right subtree of a node is **strictly greater** than the node's value.
- Both subtrees are themselves valid BSTs.

Return the list of root nodes, one for each unique BST. Two BSTs are considered structurally identical if they have the same node arrangement (the values stored are fixed: `1..n`), regardless of where they appear in the list.

The result may be returned in any order.

## Function Signature

```python
def solve(n: int) -> list[TreeNode]:
    ...
```

`TreeNode` is the usual binary tree node:

```python
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right
```

## Input / Output Convention

Input is read as a single line from stdin containing one integer `n`:

```
CASE0=<n>
```

For example:

```
CASE0=3
```

Output is written to stdout as a parenthesized, level-order (breadth-first) serialization of every generated tree, one tree per line. An empty subtree is rendered as `#`, and trees on the same case are separated by a single space on the line. (No `CASE0=` prefix on output lines.)

For `n = 3` the expected output line is:

```
1 # # 2 # 3 # # 1 # 2 # 3 # # # 1 # # 2 # 3 # # 1 # 2 # 3 # #
1 # # 1 2 # # 3 # # #
```

(tree count = Catalan(3) = 5; each tree is rendered so that consecutive lines concatenate one full rendering per tree.)

## Notes

- `n = 0` must return an empty list (no BSTs).
- The number of trees produced for general `n` is the *n*-th Catalan number; expect up to Catalan(8) = 1430 trees for `n = 8`.
- The order in which trees appear in the output is not graded beyond structural correctness and the standard parenthesization ordering used by the reference solution.
- Do not print the `CASE0=` prefix on output; it only appears in the input line.
