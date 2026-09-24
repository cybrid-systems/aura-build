# Delete Node in a Linked List

## Problem

You are given a node `node` inside a **singly linked list** (not the tail node). The node's value and a reference to its next node are known, but the head of the list is **not** given. Remove this node from the list.

After removal, the list should look as if the value of `node` never existed: copy the next node's value into `node`, then bypass the next node by linking `node.next` to `node.next.next`. The memory of the original next node may be left unreachable.

### Function Signature

Write a function with the following signature (language-agnostic):

```text
solve(node):
    # node is guaranteed to be non-null and not the tail
    # mutate node so it takes on the value of its successor
    # and skip over that successor
```

### Constraints

- `1 <= length of the list <= 1000`
- The given `node` is **not** the last node of the list.
- All node values are integers.

## Input / Output (Aura harness, `CASE0` style)

The harness builds the linked list from a `CASE0` block and only hands the
target `node` to your `solve` function. After your mutation, the harness
prints the resulting list on one line, space-separated.

Example `CASE0` block:

```text
CASE0
4 5 1 9        <- list values
1              <- index (0-based) of the node to delete
```

Meaning: build `4 -> 5 -> 1 -> 9`, and `solve` receives the node whose
value is at index `1` (the node containing `5`). Expected printed output:

```text
4 1 9
```

### Notes

- You only have a pointer to the **node to delete**, not to the head, so
  a classic "find the predecessor and unlink" approach is not possible.
- You are allowed to leave the original successor node unreachable (no
  explicit free required in this harness).
- Edge case: deleting a node whose successor is `None` is explicitly
  excluded by the constraints.
