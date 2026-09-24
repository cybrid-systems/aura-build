# Split Linked List in Parts

## Problem

Given the head of a singly linked list and an integer `k`, split the list into `k` consecutive parts. The parts should be as evenly sized as possible: that is, any two parts may differ in size by at most one, and the earlier parts must be at least as large as the later parts.

Each part should be a list whose nodes are the original list's nodes in the same order, and the parts themselves must appear in the original order. The nodes in each part should remain connected, and the dangling end of each part (if any) should be set to `null`.

Return an array (or vector) of length `k` containing the `k` parts.

- If the list has `n` nodes, then `n / k` nodes go into the first `n % k` parts, which each get one extra node.

## Function Signature

```python
def solve(head: ListNode | None, k: int) -> list[ListNode | None]:
    ...
```

## Input / Output Convention

The harness feeds parameters directly to `solve`; no stdin is used. For reference, an equivalent `CASE0` line would look like:

```
CASE0 head=[1,2,3,4,5,6,7,8,9,10] k=3
```

The function must return the array of part heads. For the example above, the expected result is the three heads of `[1,2,3,4]`, `[5,6,7]`, `[8,9,10]`.

## Notes

- `k` may be larger than the length of the list; in that case, the leading parts contain one node each and the remaining entries are `null`.
- The original list is not required to be preserved beyond what is returned; each node should belong to exactly one returned part.
- Aim for an O(n) time solution with a single pass to determine length followed by a second pass to cut the list.
