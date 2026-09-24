# Binary Tree Zigzag Level Order Traversal

## Statement
Given the root of a binary tree, return the zigzag level order traversal of its nodes' values. Traverse the tree level by level, but alternate the direction of each level: the first level is read left-to-right, the next level right-to-left, then left-to-right again, and so on. Return the collected values as a list of lists, one inner list per level.

## Input
A single test case provided as plain text on stdin (already pre-parsed by the harness into a Lisp-style structure on the `CASE0` variable). The structure represents a binary tree in the form used by the harness, e.g.:

```
CASE0=(ROOT (NODE (VAL 1) (LEFT (VAL 2)) (RIGHT (VAL 3))) (RIGHT (VAL 4)))
```

- `VAL` denotes an integer node value.
- `LEFT` and `RIGHT` may be omitted to indicate a missing child, or be another `NODE` / `ROOT` form.
- A tree may be empty (`NIL` or no `VAL`); in that case, return an empty result.

## Output
Print the zigzag level order traversal, formatted as one line per level using the harness's list notation, e.g.:

```
(LEVEL (1 3 2) (LEVEL (4 5 6 7)))
```

Use exactly the same printer the harness expects (see its `OUTPUT-FORMAT` convention). If the tree is empty, print the appropriate empty marker (e.g. `(NIL)`).

## Function Signature
```lisp
(defun solve (case)
  ;; case: the parsed CASE0 tree structure
  ;; returns a list of levels in zigzag order
  ...)
```

## Notes
- Use a queue (FIFO) to perform standard level order traversal, but reverse every other level's collected list before pushing it into the result.
- An alternative stack-based approach works too: alternate between pushing children left-to-right and right-to-left, but a queue with periodic reversal is the expected pattern for this category.
- Time complexity: O(n). Space complexity: O(n) for the queue and result.
- Leaf nodes have no `LEFT`/`RIGHT` fields; missing children should be skipped rather than treated as zero-valued nodes.
