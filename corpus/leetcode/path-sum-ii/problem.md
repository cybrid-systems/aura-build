# Path Sum II

## Problem

Given the root of a binary tree and an integer `target`, return **all** root-to-leaf paths whose node values sum to `target`. Each path must be listed in the order the nodes appear from root to leaf. The order of paths in the answer does not matter.

### Function signature

```lisp
(solve root target) -> list-of-lists
```

- `root` is the root node of a binary tree (use the convention `nil` for an empty tree).
- `target` is an integer.
- Return a list of paths, where each path is a list of node values along a root-to-leaf route.

### Input

The tree is provided **pre-encoded** in the `CASE` lines, one tree per case:

```
CASE0=NIL
CASE0_ROOT=10
CASE0_L=5,15
CASE0_R=
CASE0_NL=3,7
CASE0_NR=
CASE1=...
```

Conventions:

- `NIL` means the tree is empty; for that case, no `_ROOT`, `_L`, `_R` lines appear and the answer is an empty list.
- Otherwise, `_ROOT` is the root value (an integer). `_L` and `_R` are the **child indices** of the root, comma-separated, where `0` refers to the left child and `1` to the right child. A blank `_L` / `_R` means that side is missing.
- For every non-leaf node index `k`, there is a matching pair of lines `CASEi_L_k` and `CASEi_R_k` giving the indices of its two children. Indices are contiguous integers starting from `0` (the root); a tree with `n` nodes uses indices `0..n-1`.
- `_NL*` / `_NR*` are auxiliary lines used for nested nodes and follow the same rules as `_L` / `_R`.

### Output

For each case, print one line containing the answer as a flat S-expression of path values, e.g.:

```
()
((5 8))
((1 2) (1 3))
```

Print an empty list `()` if there are no qualifying paths.

### Notes

- A *leaf* is a node with no children on either side; paths terminate at leaves.
- Node values and the target may be negative, zero, or positive.
- If the root is `NIL`, return `()`.
