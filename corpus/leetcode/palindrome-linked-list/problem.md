# Palindrome Linked List

## Problem Statement

Given the head of a singly linked list, determine whether the list's values form a **palindrome** — that is, they read the same forward and backward.

Your solution must run in **O(n)** time and **O(1)** extra space (apart from a few pointer variables). To achieve this, use the slow/fast pointer technique to locate the middle of the list, reverse the second half in place, then compare the two halves node by node.

You are given the **head** of the list as a flat sequence of integer node values. The list has at least one node.

## Function Signature

```
def solve(head: ListNode | None) -> bool
```

- `head`: the first node of a singly linked list (or `None` for an empty list, though by problem constraints the list has at least one node).
- **Returns**: `True` if the list is a palindrome, `False` otherwise.

## Input / Output Convention

The harness reads cases from a baked-in list, not from stdin. Each case is described by two lines:

```
CASE0=<index_of_the_case>
HEAD=1 2 3 2 1
```

- `CASE0=<n>` selects which case to run (0-indexed). The harness feeds the corresponding `HEAD` line into your `solve` function as a linked list.
- `HEAD=` is a space-separated sequence of node values from the first node to the last. For example, `HEAD=1 2 3 2 1` represents the list `1 -> 2 -> 3 -> 2 -> 1`, and the expected answer is `True`. A line `HEAD=1 2 3` would be `False`.

Your function's boolean return value is compared against the expected verdict; the harness prints the result.

## Notes

- Use the **slow/fast pointer** pattern: advance `slow` by one and `fast` by two each step; when `fast` reaches the end, `slow` is at the middle.
- For even-length lists, `slow` lands on the start of the second half; for odd-length lists, it lands on the middle node — in either case, reverse the half starting at `slow.next` (or `slow`, depending on convention) and walk both halves together to compare values.
- Restore the list (re-reverse the second half) before returning so the structure is left intact — this is good practice though not strictly required by the judge.
- Do not collect values into an array; that would violate the O(1) auxiliary-space requirement.
