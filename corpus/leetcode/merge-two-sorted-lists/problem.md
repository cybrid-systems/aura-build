# Merge Two Sorted Lists

## Problem

You are given the heads of two sorted linked lists, `list1` and `list2`. Merge the two lists into one sorted list by splicing together the nodes of the first two lists. Return the head of the merged list.

The nodes are provided in non-decreasing order, and the result must also be in non-decreasing order.

## Function Signature

```python
def solve(list1: ListNode | None, list2: ListNode | None) -> ListNode | None:
    ...
```

A `ListNode` is defined as:

```python
class ListNode:
    def __init__(self, val: int = 0, next: ListNode | None = None):
        self.val = val
        self.next = next
```

## Input

The lists are given in the standard Aura "CASE0" line format. The first line after `CASE0=` is the count `n` of `list1`, followed by `n` space-separated integer values. The next line is the count `m` of `list2`, followed by `m` space-separated integer values.

Example:

```
CASE0=3 1 2 4
CASE0=3 1 3 4
```

## Output

A single line under `CASE0=` containing the values of the merged linked list, space-separated. For an empty result, print a blank line.

Example output for the input above:

```
CASE0=1 1 2 3 4 4
```

## Notes

- Both input lists are already sorted ascending; do not re-sort the values globally, only merge.
- A dummy-head (sentinel) node simplifies the merging logic and avoids special-casing the first node.
