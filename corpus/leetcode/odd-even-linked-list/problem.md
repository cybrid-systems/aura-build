# Odd Even Linked List

## Problem

Given a singly linked list, rearrange it **in place** so that all nodes at **odd positions** (1st, 3rd, 5th, …) come first, followed by all nodes at **even positions** (2nd, 4th, 6th, …). The relative order among odd-indexed nodes and among even-indexed nodes must be preserved.

Indexing is **1-based** from the head.

### Examples

**Example 1**
- Input: `1 -> 2 -> 3 -> 4 -> 5`
- Output: `1 -> 3 -> 5 -> 2 -> 4`

**Example 2**
- Input: `2 -> 1 -> 3 -> 5 -> 6 -> 4 -> 7`
- Output: `2 -> 3 -> 6 -> 7 -> 1 -> 5 -> 4`

**Example 3**
- Input: `1`
- Output: `1`

**Example 4**
- Input: `1 -> 2`
- Output: `1 -> 2`

### Constraints

- Number of nodes `n` is between `1` and `10^5`.
- Node values are arbitrary integers.

### Function Signature

```
solve(head: Node) -> Node
```

`Node` is a standard singly linked list node with fields `val` and `next`.

## I/O Convention (Aura harness)

The input is read line by line. Each line describes one test case using the following format:

```
CASE0=<head_id>
HEAD_<head_id>=<list_repr>
TAIL_<head_id>=<list_repr>
```

`<list_repr>` is a space-separated sequence of integer node values, or `EMPTY` for an empty list.

Lines not matching this format are ignored. Processing stops at end of input. The harness creates the linked list for each `HEAD_/TAIL_` pair, calls `solve(head)`, and verifies that the returned list matches the expected ordering.

### Notes

- The result is a list that starts with the original odd-indexed nodes (in order) followed by the original even-indexed nodes (in order).
- `n = 1` (a single node) and `n = 2` are included to verify the base cases.
- An `EMPTY` input list is not produced by the generator, but defensive handling is recommended.
