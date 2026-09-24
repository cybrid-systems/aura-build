# Swap Nodes in Pairs

## Statement

Given the head of a singly linked list, swap every two adjacent nodes and return the new head. Each pair of neighboring nodes (nodes at positions 1 & 2, 3 & 4, 5 & 6, …) should have their values and links exchanged.

You must swap the **nodes themselves**, not merely their values. The list length is in the range `[0, 100]`.

### Examples

`CASE0=1->2->3->4`
Expected output: `2->1->4->3`

`CASE0=`
Expected output: ``  (empty list remains empty)

`CASE0=1`
Expected output: `1`  (single node is unchanged)

## Function Signature

```
(solve head)
```

- `head` — the head node of a singly linked list, or `nil` if empty. Each node has integer fields `val` and `next`.
- **Return** — the new head after swapping every adjacent pair.

## I/O Convention

The harness provides the input on a single line through the special `CASE0` variable:

```
CASE0=<arrow-separated linked list, e.g. 1->2->3->4 or empty>
```

Your `solve` function receives the parsed list as its argument. The output should be a string formatted with `"->"` separators (or empty string for the empty list), printed by the harness wrapper.

## Notes

- The number of nodes may be odd; in that case the final node stays in place.
- Aim for O(n) time and O(1) extra space (in-place pointer rewiring). Recursive and iterative approaches are both valid.
- Be careful to update the `next` pointers in the correct order to avoid losing the rest of the list.
