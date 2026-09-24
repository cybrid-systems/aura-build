# Validate Binary Search Tree

## Problem

Given the root of a binary tree, determine if it is a **valid Binary Search Tree (BST)**.

A BST is defined as follows:

- The left subtree of a node contains only nodes with keys **strictly less than** the node's key.
- The right subtree of a node contains only nodes with keys **strictly greater than** the node's key.
- Both the left and right subtrees must also be valid BSTs.

The tree is represented as a flat array in **level-order** (breadth-first) form, where `null` denotes the absence of a child. For example, the array `[5, 1, 4, null, null, 3, 6]` encodes:

```
        5
       / \
      1   4
         / \
        3   6
```

This tree is **not** a valid BST because node `3` (in the left subtree of `4` by position) is greater than `4`, violating the ordering constraint.

## Input

The input is provided as a single line on stdin containing a level-order array literal of integers and `null`s, separated by commas.

For example:

```
[2,1,3]
```

The array length `n` is in `[0, 300]`, and integer values are in the range `[-10^9, 10^9]`. An empty array `[]` represents an empty tree, which is a valid BST.

## Output

Print `true` if the tree is a valid BST, otherwise `false`.

## Function Signature (suggested)

```python
def solve(case0: list) -> bool:
    ...
```

## I/O Convention (Harness)

The harness reads one line from stdin in the form:

```
CASE0=<python-list-literal>
```

For example:

```
CASE0=[2,1,3]
```

Parse the value after `CASE0=` and pass it (as a list) to `solve`.

## Notes

- Equality is **not** allowed between a node and its descendants; the constraints are strictly less than / strictly greater than.
- A naive approach that only checks immediate parent-child pairs is insufficient — you must verify the full `(min, max)` interval for every subtree. Consider an iterative in-order traversal and confirm that values appear in strictly increasing order.
