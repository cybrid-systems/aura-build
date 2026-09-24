# Linked List Cycle

## Problem

Given the head of a singly linked list, determine whether the list contains a cycle. A cycle exists if some node's `next` pointer points back to a previously visited node, forming a loop. Visiting a node that is already part of the list more than once means traversal never terminates.

You should return whether a cycle is present **without modifying** the list.

## Function Signature

```python
def solve(head: ListNode | None) -> bool:
    ...
```

Where `ListNode` is:

```python
class ListNode:
    def __init__(self, val: int = 0, next: 'ListNode | None' = None):
        self.val = val
        self.next = next
```

## Input / Output

The harness feeds a single test case. The first line gives the values of the linked list in order, terminated by `END`. After `END`, if the line contains a single integer `k`, the last node's `next` pointer is wired to the node at **0-indexed** position `k` to create a cycle; if absent or `-1`, the list is treated as acyclic (tail's `next` remains `None`).

Read tokens from `CASE0=...` lines. The output is `true` if a cycle exists, otherwise `false`.

### Example

```
CASE0=3 2 0 -4 END 1
```

This represents the list `3 → 2 → 0 → -4` with the tail (`-4`) pointing back to node index `1` (value `2`). Expected output: `true`.

```
CASE0=1 2 END
```

Expected output: `false`.

## Notes

- Use Floyd's cycle-finding algorithm: a slow pointer advancing one step per move and a fast pointer advancing two steps. If they ever coincide, a cycle exists; if the fast pointer hits `None`, the list is acyclic.
- The list may contain duplicate values, so value-based detection is not reliable — rely only on pointer identity.
- Expected complexity: O(n) time and O(1) extra space.
