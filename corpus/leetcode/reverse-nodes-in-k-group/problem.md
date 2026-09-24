# Reverse Nodes in k-Group

## Problem Statement

Given a singly linked list, reverse the nodes of the list **k** at a time, and return the modified list.

- **k** is a positive integer that is less than or equal to the length of the linked list.
- If the number of nodes is **not** a multiple of **k**, then the remaining nodes at the end should stay in their original order.
- You may not alter the values in the list's nodes; only the pointers between nodes may be changed.

The relative order of the nodes within each group of **k** must be reversed. Consecutive groups are not merged together — the list must preserve the boundary between every chunk of **k** nodes.

Write a function `solve(head, k)` that takes the head of the linked list and the integer **k**, and returns the new head of the modified list.

## Function Signature

```python
def solve(head: ListNode, k: int) -> ListNode:
```

Where `ListNode` is a standard singly-linked list node with `val` and `next` fields.

## Input / Output Convention

The harness will provide input via a single file `stdin.txt` in the following format, **no separate function calls**:

```
CASE0=1->2->3->4->5
CASE0_K=2
CASE1=1->2->3->4->5
CASE1_K=3
CASE2=1->2->3->4->5->6->7->8
CASE2_K=4
```

- `CASEi=` line: the linked list for test case `i`, formatted as `val1->val2->...->valN` where values are integers (may be negative). `1` denotes a single-node list. An empty list is not used.
- `CASEi_K=` line: the group size **k** for test case `i`.

The output file should contain one line per test case, in the same order as input, with the resulting linked list in the same `val1->val2->...->valN` format:

```
ANS0=2->1->4->3->5
ANS1=3->2->1->4->5
ANS2=8->7->6->5->4->3->2->1
```

## Examples

### Example 1
```
Input list:  1 -> 2 -> 3 -> 4 -> 5
k:           2
Output:      2 -> 1 -> 4 -> 3 -> 5
```
Explanation: (1,2) and (3,4) are reversed in groups of 2; the trailing `5` is left as-is because fewer than **k** nodes remain.

### Example 2
```
Input list:  1 -> 2 -> 3 -> 4 -> 5
k:           3
Output:      3 -> 2 -> 1 -> 4 -> 5
```
Explanation: Only one full group of 3 fits, so `(1,2,3)` is reversed and `(4,5)` is left untouched.

## Notes

- Node values must remain unchanged; only `.next` pointers may be rewired.
- The space complexity of an in-place reversal (using **O(1)** or **O(k)** extra pointers for the reversal walk) is expected.
- Be careful with edge cases: `k == 1` (no change), `k` equal to or larger than the list length, and lists of length 1.
- Do **not** allocate a new list — rewire the existing nodes in place.
