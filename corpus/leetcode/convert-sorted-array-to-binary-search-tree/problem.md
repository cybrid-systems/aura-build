# Convert Sorted Array to Binary Search Tree

## Problem

You are given an integer array `nums` sorted in **strictly increasing** order. Build a **height-balanced** binary search tree (BST) from it.

A height-balanced tree is one in which the depths of the two subtrees of every node never differ by more than 1.

Return the root node of the constructed BST.

It is guaranteed that a solution exists for every possible input length.

## Function Signature

```python
def solve(nums: list[int]) -> TreeNode | None:
    ...
```

A `TreeNode` has the standard shape:

```python
class TreeNode:
    def __init__(self, val: int, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right
```

## Input Format (CASE0)

The harness reads a single JSON object from standard input with this shape:

```
CASE0={"nums": [-10,-3,0,5,9]}
```

- `nums` — the sorted integer array (length `n`, `0 ≤ n ≤ 10^5`, values fit in 32-bit signed range).

## Output Format

Print the resulting tree as a JSON object using level-order serialization (the same style used by the original LeetCode problem):

- `null` represents a missing child.
- The list ends once the last non-null node has been recorded (trailing nulls are typically omitted, but implementations may emit them; the harness compares structurally).

Example:

```
{"val":0,"left":{"val":-10,"right":{"val":-3}},"right":{"val":5,"right":{"val":9}}}
```

## Notes

- Picking the **middle** element (or the left-middle one) at each recursion guarantees balance while preserving BST order on a sorted input.
- For even-length subarrays, either of the two middle elements is acceptable as the root — both produce valid height-balanced BSTs.
- `solve(None)` or `solve([])` should return `None`, which serializes to `null`.
- Memory usage should be `O(n)`; each node is created exactly once.
