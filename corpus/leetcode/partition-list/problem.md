# Partition List

## Problem

Given the head of a singly linked list and an integer `x`, rearrange the list so that all nodes with a value **less than** `x` appear before all nodes with a value **greater than or equal to** `x`. The relative order of nodes within each partition must be preserved. The function should return the head of the rearranged list.

## Function Signature

```python
def solve(head: Node, x: int) -> Node:
    pass
```

## Input / Output Convention

The harness feeds each test case into `solve` directly. There is no stdin/stdout parsing. Each invocation corresponds to one `CASE` block below the solution stub:

```
CASE0 = ...
CASE0_EXPECTED = ...
CASE1 = ...
CASE1_EXPECTED = ...
...
```

- `CASE0` (and subsequent) provides the constructor arguments as a tuple, e.g. `(list_values, x)`.
- `CASE<N>_EXPECTED` provides the expected return value as the same shape used in inputs (a `Node` built from a list), so the harness compares structurally, not by identity.

## Notes

- The list may be empty; return `None` in that case.
- Do not mutate the `val` fields of any node; only the `next` pointers may be rearranged.
- A naive "filter then concatenate" into two auxiliary lists (one for nodes `< x`, one for nodes `>= x`) is the intended approach — both lists must be built in a single forward pass to keep relative order.
