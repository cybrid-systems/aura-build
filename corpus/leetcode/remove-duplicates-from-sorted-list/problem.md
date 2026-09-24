# Remove Duplicates from a Sorted List

## Problem Statement

Given the head of a **sorted** singly linked list, delete all duplicate values so that each value appears only once. Return the head of the modified list. The list is already sorted in non-decreasing order, so duplicates are guaranteed to be adjacent.

## Function Signature

```python
def solve(head: ListNode | None) -> ListNode | None:
    ...
```

Where `ListNode` is defined as:

```python
class ListNode:
    def __init__(self, val: int = 0, next: 'ListNode | None' = None):
        self.val = val
        self.next = next
```

## Input/Output Convention (CASE lines)

The harness reads/writes a single line per case in the following format:

- **Input line (`CASE0=...`)**: First, the list length `N`, followed by `N` integer values representing the list in order from head to tail.
  Example: `CASE0=N=5;vals=1,1,2,3,3`
- **Output line (`CASE0=...`)**: The resulting list after deduplication, formatted as comma-separated values starting from the head.
  Example: `CASE0=vals=1,2,3`

For an empty input list (`N=0`), the output is `CASE0=vals=` (empty list).

## Notes

- The input list is guaranteed to be sorted in non-decreasing order.
- The relative order of distinct elements must be preserved.
- Only O(1) extra space (excluding the input/output list nodes) is expected — mutate the list in place rather than copying nodes.
- If `head` is `None`, return `None`.
