# Sum of Left Leaves

## Problem

Given the root of a binary tree, compute the **sum of all left leaves** in the tree.

A leaf is a node that has no children. A left leaf is a leaf that is the left child of its parent.

## Function Signature

```lisp
(defun solve (root)
  ...)
```

- `root` is a cons cell representing the binary tree node in the shape `(value left right)`, where `left` and `right` are either subtrees in the same shape or `nil` (empty). The root value itself is a number.
- Return the integer sum of all values stored in nodes that are **left leaves**.

## Input

The input is provided via the `CASE0` environment variable as a single S-expression. For example:

```
CASE0=("(3" "(2" "(nil" "nil)" "(nil" "nil))" "(2" "(4" "(nil" "nil)" "(nil" "nil))" "(5" "(nil" "nil)" "(6" "(nil" "nil)" "(nil" "nil)))" "(nil" "nil))")
```

Tokens describe the tree in a serialized list format. You must read `CASE0` and parse it into a tree structure before invoking `solve`.

## Output

Print a single integer — the sum of all left leaves — to standard output followed by `nil`.

## Examples

**Example 1**

Tree:
```
      3
     / \
    2   2
       / \
      5   6
```

Left leaves are: `2` (root's left subtree leaf) and `5` (left child of the right subtree leaf).
Output: `7`

**Example 2**

Tree:
```
    1
   / \
 2    3
```

Left leaves: `2`. Output: `2`

## Notes

- An empty tree (`nil`) returns `0`.
- A node is a left leaf **only if** it is itself a leaf (both children are `nil`) **and** it is the left child of its parent.
- Constraints (typical): up to `10^4` nodes; node values fit in standard integers.
