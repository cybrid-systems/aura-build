# Same Tree

## Problem

Given the roots of two binary trees `p` and `q`, determine whether they are exactly the same — both **structurally identical** and with **equal node values** at every corresponding position.

Two binary trees are considered the same if:

- They are structurally identical (same shape, same parent–child layout), and
- Every pair of corresponding nodes holds the same value.

---

## Input / Output Convention

This task is run on an **Aura** harness with a fixed input file. The relevant lines look like:

```
CASE0=call(solve, p, q)
```

- `p` and `q` are the root nodes of the two binary trees being compared, provided by the harness.
- Each tree is given in level-order (BFS) representation. `null` denotes an absent child.
- The expected return value is a boolean (`True` / `False`) wrapped according to the harness's serialization (typically `True` or `False`).

Example tree encodings the harness may produce:

- `[1, 2, 3]` → root `1`, left child `2`, right child `3`
- `[1, 2, null, null, 3]` → root `1`, left `2` (which has a right child `3`), no other children
- `[]` → empty tree (root is `null`)

---

## Function Signature

You will need to implement (or have the harness call) a function with the following shape:

```python
def solve(p: TreeNode, q: TreeNode) -> bool:
    ...
```

- `p`, `q`: root nodes of the two trees (each may be `None`).
- Returns `True` if the two trees are identical, otherwise `False`.

---

## Examples

**Example 1**

- `p = [1, 2, 3]`
- `q = [1, 2, 3]`
- Output: `True`

Both trees have root `1`, left child `2`, right child `3`, and matching values everywhere.

**Example 2**

- `p = [1, 2]`
- `q = [1, null, 2]`
- Output: `False`

Different structure: `p`'s node `2` is a left child, while in `q` it is a right child.

**Example 3**

- `p = [1, 2, 1]`
- `q = [1, 1, 2]`
- Output: `False`

Same shape but different values at the children.

**Example 4**

- `p = []`
- `q = []`
- Output: `True`

Two empty trees are considered the same.

---

## Notes

- A `null` node matches another `null` node at the same position; any other mismatch in structure (one side missing while the other is present) immediately makes the trees different.
- A simple recursive traversal (DFS) comparing node pairs is sufficient; a BFS/iterative approach is also acceptable.
- Mind the edge case where both inputs represent empty trees — they must be reported as the same tree.
