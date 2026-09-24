# Merge Two Binary Trees

## Problem

You are given two binary trees, `t1` and `t2`. Imagine that when you overlay `t1` on top of `t2`, some nodes of the two trees are overlapped while others are not. Your task is to merge the two trees into a new binary tree as follows:

- If two nodes overlap (both exist at the same position), the merged node's value is the sum of the two nodes' values.
- If only one node exists at a position (the other is `null`), the merged tree uses that node as-is.

Return the root of the merged tree.

## Function Signature

```lisp
(defun solve (t1 t2)
  ;; t1 and t2 are tree roots (or NIL).
  ;; Return the root of the merged tree.
  )
```

The trees are represented as nested lists in Lisp style: a node is `(value left right)`, where `left` and `right` are either subtrees or `NIL`. For example, the tree

```
    1
   / \
  3   2
 / \
5   4
```

is represented as `(1 (3 (5 NIL NIL) (4 NIL NIL)) (2 NIL NIL))`.

## Input / Output Convention

The harness invokes `solve` directly; there is no stdin reading. Instead, the test harness feeds cases via a leading comment block at the top of the file:

```
;; CASE0: t1=(1 (3 (5 NIL NIL) (2 NIL NIL)) (NIL NIL NIL))  t2=(2 (1 NIL (4 NIL NIL)) (3 NIL NIL))
;; CASE1: t1=(NIL NIL NIL)  t2=(NIL NIL NIL)
;; CASE2: t1=(1 NIL NIL)  t2=(2 (3 NIL NIL) (NIL NIL))
```

For each `CASEi`, the harness binds `t1` and `t2` to the given literals and calls `(solve t1 t2)`. The expected return is the merged tree in the same ` (value left right) ` nested-list format (with `NIL` for empty subtrees).

## Examples

**Example 1**
```
t1 = (1 (3 (5 NIL NIL) (NIL NIL NIL)) (2 NIL NIL))
t2 = (2 (1 NIL (4 NIL NIL)) (3 NIL NIL))
```
Merged tree:
```
       3
      / \
     4   5
    / \   \
   5   4   7
```
Encoded: `(3 (4 (5 NIL NIL) (4 NIL NIL)) (5 (NIL NIL NIL) (7 NIL NIL)))`

**Example 2**
```
t1 = (NIL NIL NIL)
t2 = (1 (2 NIL NIL) (3 NIL NIL))
```
Merged tree is simply `t2`: `(1 (2 NIL NIL) (3 NIL NIL))`.

**Example 3**
```
t1 = (1 NIL NIL)
t2 = (2 (3 NIL NIL) (NIL NIL NIL))
```
Merged tree: `(3 (3 NIL NIL) (NIL NIL NIL))`.

## Notes

- Both `t1` and `t2` may be `NIL`; the merge of two empty trees is `NIL`.
- The original input trees must not be mutated; construct and return a fresh tree.
- A straightforward recursive solution runs in `O(min(n1, n2))` time, which is optimal — you only need to visit nodes that exist in *both* trees, plus any extra nodes of the larger one.
