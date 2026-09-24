# Flatten Binary Tree to Linked List

## Problem

Given the `root` of a binary tree, flatten it into a "linked list" in-place following the **preorder** traversal order (root → left subtree → right subtree).

After flattening:

- Each node's `left` child should be `None`.
- Each node's `right` child should point to the next node in the preorder sequence.
- The order of nodes must match a preorder traversal of the original tree.
- You must modify the tree in-place; do not allocate a new list of nodes.

For example, a tree

```
    1
   / \
  2   5
 / \   \
3   4   6
```

flattens to

```
1
 \
  2
   \
    3
     \
      4
       \
        5
         \
          6
```

## Input

The input is provided on stdin as a description of the tree in the harness's `CASE0=...` format.

- `CASE0_N=<integer>` — number of nodes in the tree.
- `CASE0_NODES=<space-separated integers>` — the values of the nodes in level-order (breadth-first) sequence. Use `-1` (or the configured null sentinel) to indicate an absent child.

Example:

```
CASE0_N=6
CASE0_NODES=1 2 5 3 4 -1 6
```

## Output

The flattened tree, encoded in the same level-order format as the input (with `None`/`-1` for absent children), terminated by a newline. After flattening, each node's left child is `None`, so the output degenerates into a right-skewed chain.

For the example above, the output would be:

```
1 -1 2 -1 3 -1 4 -1 5 -1 6
```

## Function Signature

```python
def solve(root) -> None:
    ...
```

`root` is the root of the binary tree (or `None` if the input tree is empty). The function should mutate `root` in place and return nothing.

## Notes

- You may assume the tree contains at most `10^4` nodes and node values fit in a standard signed integer range.
- The flattening must be done in-place; recursive or iterative solutions with `O(1)` extra space (excluding the call stack) are ideal, but `O(n)` auxiliary space solutions are also accepted.
- An empty tree should yield an empty output.
