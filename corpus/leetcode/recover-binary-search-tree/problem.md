# Recover Binary Search Tree

## Problem

You are given the root of a Binary Search Tree (BST) in which exactly two of the nodes have had their values swapped by mistake. As a result, the tree no longer satisfies the BST property.

Your task is to fix the tree by swapping the values of those two nodes back, **without changing the structure** of the tree. After the recovery, the tree must be a valid BST.

The tree contains `n` nodes, where `2 ≤ n ≤ 10^4`. Node values are unique integers in the range `[-10^9, 10^9]`.

## Input

The tree is provided in level-order (breadth-first) format, one node per slot, where `null` represents the absence of a child.

```
CASE0=root=4 3 7 null null 2 6
```

## Output

Print the recovered tree in the same level-order format as the input, using `null` for absent children. Trim trailing `null`s so that only the structural slots required to represent the tree are emitted.

```
CASE0=2 3 5 1 4 6 7
```

## Function signature

```lisp
(solve root) -> fixed-tree
```

`root` is the tree as a structure (list with `null` children, etc.); return the fixed tree in the same representation.

## Notes

- In-order traversal of a BST visits nodes in sorted order. The two swapped values create one or two “inversions” in that ordering — use them to locate the misplaced nodes in **O(n)** time and **O(h)** auxiliary space.
- An iterative in-order traversal with a single previous-pointer avoids recursion and works comfortably within the limits.
- All node values are distinct, so the two swapped nodes are uniquely identifiable.
