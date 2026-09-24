# Symmetric Tree

## Statement

You are given the root of a binary tree. Determine whether the tree is **symmetric** — that is, a mirror image of itself about its center.

Two trees `a` and `b` are mirrors of each other when:
- Both nodes are `null`, **or**
- Both nodes are non-null, their values are equal, and:
  - `a.left` is a mirror of `b.right`, **and**
  - `a.right` is a mirror of `b.left`.

An empty tree (a `null` root) is considered symmetric.

## Function Signature

```clojure
(solve root)
```

- `root` — the root node of a binary tree, given in the harness-specific tree encoding (see I/O convention).
- Returns `true` if the tree is symmetric, otherwise `false`.

## Input / Output Convention

Input is provided as a single `CASE0=...` line containing the serialized tree, using **level-order** (BFS) encoding with `null` for missing children, terminated by `#`.

```
CASE0=(1 (2 (3 # #) (4 # #)) (2 (4 # #) (3 # #)))#
```

Output: a single line with the boolean result.

```
true
```

## Notes

- The serialization uses parentheses to delimit nodes, with `null` for absent children. The line ends with `#`.
- A single-node tree and the empty (null) tree are both symmetric.
- You only need to compare the root's left and right subtrees for mirrored structure and equal values.
