# Binary Tree Level Order Traversal

Given the root of a binary tree, return the level order traversal of its nodes' values from left to right, level by level.

## Input

A single test case consisting of one line describing a binary tree in level-order (BFS) array form, similar to LeetCode's serialization:

- The root value comes first.
- For each node at index `i` (0-indexed), its left child is at index `2*i + 1` and its right child is at index `2*i + 2`.
- A node with no child is represented by `#` (or any non-numeric placeholder).
- Values are integers; tokens are separated by spaces.

Example input:
```
3 9 20 # # 15 7
```

This describes:
```
        3
       / \
      9   20
         /  \
        15   7
```

## Output

Print one line per level, each line containing the values of that level separated by a single space. Levels are printed from top (root) to bottom. Trailing spaces are allowed.

For the example above, the expected output is:
```
3
9 20
15 7
```

## Function Signature

```clojure
(solve tree-array)
```

- `tree-array`: a sequence of strings (tokens from the input line), where each token is either an integer string or `#`.
- Returns: a sequence of sequences of integers, one inner sequence per level, from top to bottom.

## Notes

- An empty tree is represented by a single `#` token; the expected output is a single empty line.
- Use a queue (FIFO) to perform BFS level by level, separating levels by recording the queue's size before each iteration.
- The tree depth is bounded only by the input size; the algorithm must run in `O(n)` time and `O(n)` extra space.
