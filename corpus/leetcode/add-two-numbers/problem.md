# Add Two Numbers

## Problem

You are given two non-empty linked lists representing two non-negative integers. The digits are stored in **reverse order**, and each node contains a single digit. Add the two numbers and return the sum as a linked list (also in reverse order).

You may assume the two numbers do not contain any leading zeros, except the number `0` itself.

## Function Signature

```python
def solve(l1: ListNode, l2: ListNode) -> ListNode:
```

Where `ListNode` is defined as:

```python
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next
```

## Input / Output Convention

The harness reads cases from a single `stdin`-less fixture file. Each case is written as four lines:

```
CASE0=l1
CASE0_L2=l2
CASE0_EXPECT=expected
CASE0_NEXT=...
```

- `l1` and `l2` are comma-separated digit lists in **reverse order** (e.g., `2,4,3` represents the number `342`).
- `expected` is the comma-separated digit list representing the correct sum, also in reverse order.
- The final case uses `CASE0_NEXT=-1` to indicate end of input.

**Example:**

```
CASE0=2,4,3
CASE0_L2=5,6,4
CASE0_EXPECT=7,0,8
CASE0_NEXT=-1
```

This represents `342 + 564 = 807`, which reversed is `7,0,8`. ✅

## Notes

- Each linked list is non-empty and represents a non-negative integer.
- The lists may have different lengths; pad the shorter one with implicit zeros.
- Remember to carry over when the sum of digits in a column is `10` or greater.
- The result must use exactly `O(1)` extra space beyond the output list (i.e., reuse / build nodes in place; do not reverse an array).
- The output must not contain leading zeros, except for the single digit `0`.
