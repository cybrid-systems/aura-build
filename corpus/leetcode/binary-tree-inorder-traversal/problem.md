# Binary Tree Inorder Traversal

Return the inorder traversal (Left → Node → Right) of a binary tree's node values, from root to leaves.

## Input

A single binary tree provided by the harness on the `aura.tree` channel.

- `aura.tree` is a single object: `{ value: number|null, left: <tree>|null, right: <tree>|null }`, where the root node is the top-level object. A `null` value at the root denotes an empty tree.
- The tree contains at most `10^5` nodes.
- Node values are integers in the range `[-10^9, 10^9]`.

## Output

Emit one `aura.result` value:

- An array of numbers: the inorder traversal of the tree, in order from leftmost node to rightmost node.
- For an empty tree (root value is `null`), emit `[]`.

The function should be pure with respect to the input tree.

## Function Signature

```ts
function solve(aura: { tree: TreeNode | null }): number[]
```

## I/O Convention (`CASE0=...` lines)

Each case is presented as a `CASE0=...` line, where the value is the JSON-encoded tree object described above. Examples:

```
CASE0={"value":1,"left":{"value":2,"left":null,"right":null},"right":{"value":3,"left":null,"right":null}}
CASE0={"value":null,"left":null,"right":null}
```

- For `CASE0 = {"value":1,"left":{"value":2,"left":null,"right":null},"right":{"value":3,"left":null,"right":null}}`, the expected output is `2 1 3`.
- For `CASE0 = {"value":null,"left":null,"right":null}`, the expected output is an empty line.

Each case's result should be emitted on its own line in the same order as the inputs.

## Notes

- The traversal may be implemented recursively or iteratively (e.g., using an explicit stack); both are acceptable as long as the result is correct.
- The harness supplies a single tree per case via the `aura` object; do not read from `stdin`.
