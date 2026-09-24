# Linked List Cycle II

## Problem

Given the head of a singly linked list, return the node where the cycle begins, or `null` if the list has no cycle.

The list is represented as a sequence of node indices starting at `-1` (the head's predecessor). Each index points to the next node, or to `-2` to indicate the end of the list. A cycle exists if some node is reachable from itself by following `next` pointers repeatedly.

## Function Signature

```python
def solve(successors: list[int]) -> int:
```

### Parameters

- `successors`: a list where `successors[i]` is the index of the node that node `i` points to, or `-2` if node `i` is a tail (no next node). The head is the unique node whose value is `-1` in this list. (Index `-1` denotes "no previous node" and is the head marker, not a real node.)

### Returns

The index of the node where the cycle begins, or `-1` if the list is acyclic.

## Input / Output Convention (Aura harness)

The harness communicates test cases over stdin/stdout using the following simple line-based format. There is no enclosing JSON.

```
CASE0=successors=[2,0,1,4,5,3,-2]
CASE0=expected=2
CASE1=successors=[-2,0]
CASE1=expected=-1
CASE2=successors=[1,0]
CASE2=expected=0
```

- `successors=[...]` — the array as a Python-style list literal.
- `expected=...` — the index of the cycle's entry node, or `-1` if there is no cycle.

Your `solve` function should return the same value described above. The harness will parse these lines and check your function's return value against `expected`.

## Examples

**Example 1** — A cycle that includes all nodes.
- Input: `successors=[2,0,1,4,5,3,-2]` is not valid; here we use only non-negative indices plus `-2`.
- Consider nodes `0..3` with `successors = [1,2,3,0,-2]`. The cycle begins at node `0`.
- `expected=0`

**Example 2** — Tail with no cycle.
- `successors = [-2, 0]` means: node 0 is the tail (next = -2); node 1 points back to node 0... but the head marker `-1` is not present in this array, so node 1 is the head and points to node 0, which terminates.
- `expected=-1`

**Example 3** — Two-node cycle.
- `successors = [1, 0]`. Head is node 1 (the `-1` value), which points to node 0; node 0 points back to node 1.
- `expected=1`

## Notes

- Use Floyd's cycle-finding algorithm: advance a slow pointer one step and a fast pointer two steps until they meet inside the cycle; then reset one pointer to the head and advance both one step at a time — their meeting point is the cycle's entry.
- The array length `n` is at most `10^5`, and indices are within `[-2, n-1]`.
- Return `-1` when no cycle is detected.
