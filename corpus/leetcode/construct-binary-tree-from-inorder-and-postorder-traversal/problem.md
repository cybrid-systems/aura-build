# Construct Binary Tree from Inorder and Postorder Traversal

## Problem

You are given two arrays that represent the **inorder** and **postorder** traversals of a binary tree (with `null` placeholders where appropriate). Reconstruct the tree and return it.

This is a classic re-construction problem: given two traversal orders that together uniquely determine a binary tree, rebuild the structure.

## Input / Output

For this harness the problem is **single-case** (the runner does not read a length and then a list of cases; instead the test fixture is provided directly as one fixed block on standard input, formatted as `CASE0=...` lines):

```
CASE0_INORDER=[value, value, value, ...]
CASE0_POSTORDER=[value, value, value, ...]
```

- `INORDER` is the inorder traversal (left subtree, root, right subtree).
- `POSTORDER` is the postorder traversal (left subtree, right subtree, root).
- Values are integers; use a sentinel (commonly `-1` or `null`, the fixture will pick one) to denote an absent child.

Your solver must consume exactly that fixture, reconstruct the tree, and print the result in the format described below.

## Output Convention

Print the reconstructed tree using a level-order (BFS) traversal, one value per position, with the same `null` sentinel used in the input for missing children. For example, given the fixture:

```
CASE0_INORDER=[1, 2, 3, null, 5]
CASE0_POSTORDER=[1, 3, null, 5, 2]
```

your solver should print something like:

```
RESULT=[2, 1, 5, null, 3]
```

(if `null` is the chosen sentinel) — i.e. one line beginning with `RESULT=[` and ending with `]`, values comma-separated, no trailing comma.

## Function Signature (Haskell)

```haskell
solve :: IO ()
solve = do
  inorderRaw   <- readLn   -- "CASE0_INORDER=[...]"
  postRaw      <- readLn   -- "CASE0_POSTORDER=[...]"
  let inorder   = parseList inorderRaw
      postorder = parseList postRaw
      tree      = build inorder postorder  -- returns Tree
  printResult tree                         -- prints "RESULT=[...]"
```

The exact `Tree` type and the `parseList` helper are part of the harness boilerplate; you implement `build :: [Maybe Int] -> [Maybe Int] -> Tree` (or the equivalent for the harness's chosen representation) and the print routine.

## Notes

- `postorder` lets you read the root by looking at the last element; `inorder` splits the tree into the left and right subtrees around that root.
- Watch out for the duplication that the sentinel introduces: every postorder position with two `null`s and an `null` root marker still consumes indices in the inorder list in lock-step. Most clean solutions use a divide-and-conquer recursion with explicit index windows into the inorder list rather than relying on `null`-consumption rules.
- The fixture uses `null` (or `-1`, depending on the harness build) as the missing-child sentinel; match whichever one is present in the `CASE0_...` lines.
