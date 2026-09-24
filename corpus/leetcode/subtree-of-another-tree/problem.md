# Subtree of Another Tree

## Problem

Given the roots of two binary trees `root` and `subRoot`, return `true` if `subRoot` is a **subtree** of `root`. A tree `subRoot` is a subtree of `root` if there exists a node in `root` such that the subtree rooted at that node is **identical** (both structure and node values) to `subRoot`.

Write a function that, given two binary tree root nodes, returns `true` if and only if `subRoot` is a subtree of `root`.

Each node contains an integer value `val`, and references to left child `left` and right child `right` (which may be `null`).

## Function Signature

```clojure
(solve root sub-root) -> boolean?
```

- `root` and `sub-root` are tree nodes (or `nil`), where a node is a map `{:val int :left node|nil :right node|nil}`.
- Return `true` if `sub-root` is a subtree of `root`, otherwise `false`. The empty tree (`nil`) is considered a subtree of any tree.

## Input

The test cases are encoded as a single string via the `CASE0` environment variable, using a small Lisp-style S-expression notation.

**Format**

```
CASE0="(solve <root> <sub-root>)"
```

**Tree literal syntax** (Höcker-style list → tree):

- An empty tree is `()`.
- A node is `(val left right)`, where `left` and `right` are themselves tree literals.

For example, `root = [3, 4, 5, 1, 2]` and `subRoot = [4, 1, 2]` corresponds to:

```
CASE0="(solve (3 (4 (1 () ()) (2 () ())) (5 () ())) (4 (1 () ()) (2 () ())))"
```

## Output

A single boolean printed to stdout: `true` or `false`.

## Examples

**Example 1**

```
CASE0="(solve (3 (4 (1 () ()) (2 () ())) (5 () ())) (4 (1 () ()) (2 () ())))"
```
Output: `true`

**Example 2**

```
CASE0="(solve (3 (4 (1 () ()) (2 () (0 () ()))) (5 () ())) (4 (1 () ()) (2 () ())))"
```
Output: `false`  (extra node `0` in `root`'s left subtree breaks identity)

**Example 3**

```
CASE0="(solve (1 (2 () ()) (3 () ())) ())"
```
Output: `true`  (empty tree is a subtree of every tree)

## Notes

- A subtree match requires *both* identical structure and identical node values at every position.
- The empty tree `()` is a subtree of any tree, including itself.
- Node values are arbitrary integers; only equality matters, not ordering.
- A naïve solution checks every node of `root` against `subRoot` (O(n·m)). A more efficient solution uses tree hashing / serialization to achieve roughly O(n+m).
