# Reorder List

## Problem

You are given the head of a singly linked list. Reorder the list **in place** so that it follows the pattern:

```
L0 → Ln → L1 → Ln-1 → L2 → Ln-2 → …
```

In other words, the first node stays first, the last node becomes second, the second node becomes third, the second-to-last becomes fourth, and so on.

You may **not** modify the node values — only pointer rewiring is allowed. The relative order of nodes is determined purely by their original positions in the list.

### Example

Given a list `1 → 2 → 3 → 4 → 5`:

- Take the first element: `1`
- Take the last element: `5`
- Take the second element: `2`
- Take the second-to-last: `4`
- Take the middle element: `3`

So the reordered list is `1 → 5 → 2 → 4 → 3`.

For an empty list or a single-node list, the result is the same list.

## Function Signature

```python
def solve(head: Optional[ListNode]) -> Optional[ListNode]:
    ...
```

where `ListNode` is

```python
class ListNode:
    def __init__(self, val: int, next: Optional['ListNode'] = None):
        self.val = val
        self.next = next
```

## Input / Output Convention (CASE0)

The harness feeds test cases through a `CASE0` line followed by a `solve(...)` call. Each `CASE0` block looks like:

```
CASE0={
    "head": [1,2,3,4,5]
}
solve(CASE0["head"])  # -> [1,5,2,4,3]
```

The argument may be provided as:

- a Python list of integers (the harness builds the linked list for you), or
- a pre-built `ListNode` chain (already a `ListNode` with a `.next` pointer).

The function must return either a `ListNode` (the new head) or a Python list of integers. Returning `None` is valid for an empty input.

## Notes

- Aim for **O(n)** time and **O(1)** extra space (excluding recursion / stack overhead).
- A clean three-step approach is acceptable:
  1. Find the middle of the list (slow/fast pointers).
  2. Reverse the second half in place.
  3. Merge the two halves by interleaving their links.
- Edge cases to consider: 0 nodes, 1 node, 2 nodes, odd length, even length.
