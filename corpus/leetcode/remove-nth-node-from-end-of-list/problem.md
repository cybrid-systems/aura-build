# Remove Nth Node From End of List

## Problem

Given the head of a singly linked list, remove the **n-th node from the end** of the list and return the new head.

- `n` is always valid: `1 ≤ n ≤ number of nodes`.
- After removal, the remaining nodes keep their original order.
- The list is given as a standard vector/array of node values (see I/O below); you must simulate the linked-list behavior.

Your algorithm should run in **one pass** (a single traversal from head to tail), using the classic two-pointer / gap-of-`n` technique.

## Function Signature

```text
solve(head: list[int], n: int) -> list[int]
```

- `head`: the values of the linked list, in order from head to tail. May be empty? — for this problem it has at least 1 node.
- `n`: the position (1-indexed) counted from the end.
- Returns: the list of values after the target node has been removed.

## Input / Output Convention

The harness runs multiple cases. Each case is provided on **two lines** in `stdin`:

```
CASE0=head=<comma-separated ints>;n=<int>
CASE0_EXPECT=<comma-separated ints>
```

Example:

```
CASE0=head=1,2,3,4,5;n=2
CASE0_EXPECT=1,2,3,5
```

There is no other input. Parse the `CASE0=...` line to extract `head` and `n`; return the resulting list formatted as comma-separated ints (no spaces) wrapped in your solver's output wrapper as required by the harness.

## Notes

- Use a dummy/anchor node before the real head so that removing the first node works uniformly.
- Advance a "fast" pointer `n` steps ahead of a "slow" pointer, then move both until `fast` reaches the end — the node after `slow` is the one to remove.
- Single pass, O(L) time, O(1) extra space (excluding the output list).
- Edge case to keep in mind: `n` equal to the list length means removing the head.
