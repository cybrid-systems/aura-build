# Reverse Linked List II

**Category:** linked_list

## Problem

Given the head of a singly linked list and two integers `m` and `n` (1-indexed), reverse the nodes of the list **in place** from position `m` through position `n` (inclusive) in a single pass, and return the head of the resulting list.

It is guaranteed that `1 ≤ m ≤ n ≤ length(list)`. The list nodes carry integer values (you may treat the value type generically; only pointer manipulation is required by the reference solution).

## Function Signature

```
(solve head m n)
```

- `head` — the head node of a linked list (each node has `val` and `next` fields)
- `m`, `n` — 1-indexed start and end positions of the segment to reverse
- Returns — the new head of the list after the partial reversal

## Input / Output Convention (Aura harness)

The harness reads a self-describing case from a single block. A leading line selects the case:

```
CASE0=reverse_linked_list_ii
```

Subsequent lines describe the linked list and the operation. A typical encoding uses:

```
HEAD=<serialized list>            # e.g. 1,2,3,4,5   (empty => HEAD=)
M=<integer>                       # left bound (1-indexed)
N=<integer>                       # right bound (1-indexed)
```

Lines may appear in any order, but each key appears exactly once. The solver must parse the `HEAD` value, build the linked list, apply the partial reversal between positions `M` and `N`, and emit the resulting list in the same serialized form on a single line:

```
OUT=<serialized list>             # e.g. 1,4,3,2,5   (empty => OUT=)
```

## Notes

- The reversal must be performed **in one pass** over the list — do not walk the segment twice.
- A **dummy / sentinel node** pointed at `head` is the canonical trick: it lets you treat the case `m = 1` uniformly without special-casing a new head.
- Edge cases worth covering: `m == 1` (the head itself moves), `m == n` (no-op), and `n` is the last node.
