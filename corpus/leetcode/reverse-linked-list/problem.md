# Reverse Linked List

## Problem

Given the head of a singly linked list, reverse the list and return the new head.

Each node in the list contains an integer value and a pointer to the next node. The list may be empty (i.e., the head is `null`/`None`/`nullptr`); in that case, return an empty list.

## Function Signature

```python
def solve(head: Node | None) -> Node | None:
    ...
```

Where `Node` is defined as:

```python
class Node:
    def __init__(self, value: int, next: Node | None = None):
        self.value = value
        self.next = next
```

## Input / Output Convention (Aura Harness)

There is **no stdin**. The harness calls `solve(head)` directly. The input list and expected output are described in `CASE0` lines embedded in the test file, for example:

```
CASE0_INPUT_LABELS=head
CASE0_INPUT_0=null
CASE0_INPUT_1=1->2->3->4->5
CASE0_INPUT_2=1
CASE0_OUTPUT_0=null
CASE0_OUTPUT_1=5->4->3->2->1
CASE0_OUTPUT_2=1
```

- A label `null` denotes an empty list.
- A label `a->b->c` denotes a linked list with node values `a`, `b`, `c` in that order.
- A single integer `x` denotes a one-node list `[x]`.

Your implementation must reverse the list in place (or construct a reversed list) and return the new head so that iterating it left-to-right yields the reversed order.

## Notes

- Aim for **O(n)** time and **O(1)** extra space if implementing iteratively; a recursive **O(n)** solution is also acceptable.
- Be careful with edge cases: an empty list and a single-node list should both round-trip unchanged (since the reverse of one node is itself).
