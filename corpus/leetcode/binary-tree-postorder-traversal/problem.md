# Binary Tree Postorder Traversal

## Problem

Given the `root` of a binary tree, return the values of its nodes' values in **postorder** traversal order (left subtree, right subtree, root).

The tree is represented by serialized integers: each node value appears as a token, and `null` (or an empty token) marks a missing child. A `null` root represents an empty tree.

You must produce the traversal list. Either a recursive or an iterative solution is acceptable, but iterative solutions typically use an explicit stack.

## Function Signature

```
(solve root)
```

- `root`: the value at the current node, or `null`/`None` if this position is empty.
- For non-leaf nodes, child values are obtained by calling `(solve left)` and `(solve right)` as needed.

## Input

The harness invokes `(solve ...)` directly — there is **no stdin**. The test cases are wired by the runner:

```
CASE0=root=1,left=2,right=3
CASE1=root=1,left=2,right=null
CASE2=root=null
```

Each `CASE` line describes the tree by naming the `root` and its `left`/`right` subtrees in the same compact format (recursively, with `null` for missing children).

## Output

Return a list (or sequence) of node values in postorder. The runner compares it against the expected postorder sequence for each case.

## Notes

- Postorder sequence rules: visit left subtree, then right subtree, then the node itself.
- An empty tree (`null` root) should return an empty result.
- Iterative approaches commonly use two stacks, or one stack with a "last visited" pointer, to simulate the recursion without overflowing on deep trees.
- Time complexity is expected to be `O(n)` and space `O(n)` in the worst case (the output itself counts toward space).

## Example

For the tree:

```
    1
   / \
  2   3
 / \
4   5
```

Postorder traversal is: `[4, 5, 2, 3, 1]`.
