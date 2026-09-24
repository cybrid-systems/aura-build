# Unique Binary Search Trees

Given an integer `n`, compute the number of structurally unique Binary Search Trees (BSTs) that store the values `1, 2, ..., n`.

Two BSTs are considered *structurally unique* if their shapes (ignoring the actual values at each node) are different. The values themselves are always `1..n` in BST order, so only the choice of root and the recursive partitioning of the left/right subtrees matters.

## Examples

```
n = 1  -> 1
n = 3  -> 5
n = 4  -> 14
n = 5  -> 42
```

## Function Signature

```
(solve n)
  -> integer
```

`n` is a non-negative integer. Return the total count of structurally unique BSTs.

## Input / Output (Aura harness)

The harness feeds cases on standard input, one per line, in the form:

```
CASE0=1
CASE1=3
CASE2=4
CASE3=5
```

For each `CASEi=<n>` line, your `solve` is invoked with `n` and must print exactly one integer: the answer for that case, on its own line.

## Notes

- For `n = 0` there is exactly one empty tree (the empty BST), so the answer is `1`.
- This sequence is the Catalan numbers: `C(0)=1, C(1)=1, C(2)=2, C(3)=5, C(4)=14, ...`.
- A direct dynamic-programming recurrence is sufficient; no tree construction is required.
- Values of `n` may be large enough that the answer exceeds 32-bit range — use 64-bit integers (or the language equivalent).
