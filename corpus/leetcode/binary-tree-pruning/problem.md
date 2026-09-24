# Binary Tree Pruning

## Problem

You are given the root of a binary tree where every node's value is either `0` or `1`. A subtree is considered **invalid** if it contains no node with value `1` (i.e., every node in the subtree is `0`). Your task is to prune the tree by removing every invalid subtree — in other words, keep only the subtrees that contain at least one `1`, and return the root of the resulting tree.

If the entire tree becomes invalid after pruning, return `None` (or the language's equivalent of a null/empty tree).

This is the classical "Binary Tree Pruning" problem (LeetCode 814).

## Function Signature

```python
def solve(root: Optional[TreeNode]) -> Optional[TreeNode]:
    ...
```

## Input Format

The input is read from standard input. The tree is provided as a level-order (BFS) traversal, with `None` (or `null`) used to indicate absent children.

The very first line is a header of the form `CASE0=<n>`, where `<n>` is the number of test cases. Each test case then consists of two lines:

```
CASE<i>=<m>
<comma-separated node values, with "null" for missing children>
```

where `<m>` is the number of values in the level-order array (including the `null` markers). Values are either the integers `0` or `1`, or the literal string `null`.

For example:

```
CASE0=2
7
1, 1, 0, 1, 1, 0, 1, null, null, null, null, null, null, null, null
4
1, 0, 1, 0, 0, 0, 1, null, null, null, null, null, null, null, null
```

After pruning, the resulting tree should be printed (for debugging/verification) as a level-order array using the same `null`-padded format, one test case per line, prefixed with `OUT<i>=`.

## Output Format

For each test case `<i>`, print a single line:

```
OUT<i>=<comma-separated level-order traversal of the pruned tree>
```

Use `null` for missing children. If the pruned tree is empty, print `OUT<i>=null`.

## Notes

- A node is removed only if **its entire subtree** contains no `1`s. A node with value `0` whose descendants include a `1` must be kept (it is part of a valid subtree).
- The pruning is done recursively: process the left child first, then the right child, then decide whether to remove the current node.
- The input tree is guaranteed to be a valid binary tree structure (i.e., the `null` markers correctly terminate children).
- You may assume at least one test case is provided.
