# Remove Duplicates from Sorted List II

## Problem

Given the head of a sorted linked list, delete **all** nodes that have duplicate numbers, leaving only distinct numbers from the original list. Return the head of the modified list.

The list is sorted in non-decreasing order, so all occurrences of a value appear in a contiguous block.

## Function Signature

```python
def solve(head: ListNode | None) -> ListNode | None:
    ...
```

Where `ListNode` is defined as:

```python
class ListNode:
    def __init__(self, val: int = 0, next: 'ListNode | None' = None):
        self.val = val
        self.next = next
```

## Input / Output Convention

Input arrives on **standard input** as a single test case in the following `CASE0` format:

```
CASE0
<list_size>
<list_values...>
END
```

- Line 1: `CASE0` — literal marker.
- Line 2: an integer `n` (number of nodes), with `0 ≤ n ≤ 10^5`.
- Line 3: `n` space-separated integers representing the sorted list values, with `-10^4 ≤ val ≤ 10^4`. May be empty if `n == 0`.
- Line 4: `END` — literal marker.

The function `solve` receives the parsed head of the list and must return the head of the resulting list. Output is not graded line-by-line here; the harness inspects the returned list directly.

### Example

```
CASE0
8
1 2 3 3 4 4 5 6
END
```

Expected result: `1 -> 2 -> 5 -> 6` (nodes with values `3` and `4` are fully removed).

## Notes

- A sentinel/dummy node before `head` is a common technique to simplify deletion of leading duplicates.
- Since the list is sorted, duplicates of a value always form one contiguous run — you only need to decide once per run whether to keep or drop it.
- Aim for **O(n)** time and **O(1)** extra space (excluding the output list itself).
