# Intersection of Two Linked Lists

## Problem

You are given the heads of two singly linked lists `headA` and `headB`. The lists may share a suffix — that is, they may converge at some node and then continue together as a single chain. Return the reference to that first common node. If the two lists do not intersect, return `None`.

Each node has an integer value (`val`) and a `next` pointer. The lists are cycle-free.

You must solve it in **O(n + m)** time and **O(1)** extra space, where `n` and `m` are the lengths of the two lists.

## Function Signature

```python
def solve(headA: ListNode, headB: ListNode) -> ListNode | None:
    ...
```

`ListNode` is defined as:

```python
class ListNode:
    def __init__(self, val: int = 0, next: 'ListNode | None' = None):
        self.val = val
        self.next = next
```

## Input / Output Convention (harness format)

The solver is invoked with **no stdin**. Instead, the harness builds the linked lists from a `CASE0` block in the problem file:

```
CASE0 = (
    # headA: 4 -> 1 -> 8 -> 4 -> 5
    # headB: 5 -> 6 -> 1 -> 8 -> 4 -> 5
    # intersection at the node with val=8
    skip=None, val=4, next=skip   # tail of A's shared suffix is irrelevant; harness wires it
)
```

Concretely, the harness constructs two lists and (if they intersect) makes a designated node of one list the continuation of the other so that both terminate at the same node. The solver receives the two head references and must return the common node, or `None` if there is no intersection.

Example expectations (the harness compares by `is` identity on the returned node):

- Lists `A = 4->1->8->4->5`, `B = 5->6->1->8->4->5` sharing the node `8` → return that node.
- Disjoint lists `A = 2->6->4`, `B = 1->5` → return `None`.

## Notes

- The classic trick is to walk two pointers `pA` and `pB`; when either reaches the end of its list, redirect it to the other list's head. After at most `n + m` steps, the pointers either meet at the intersection or both become `None`.
- An alternative `O(n + m)` approach with hashing is allowed by the time bound but violates the space bound — prefer the pointer-switching solution.
- Be careful: return the actual node reference, not a node with an equal `val`. The harness checks node identity.
