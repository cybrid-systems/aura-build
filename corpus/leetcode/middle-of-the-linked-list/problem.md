# Middle of the Linked List

## Problem

Given the head of a singly linked list, return the **middle node** of the list.

- If the list has an odd number of nodes, the middle is the single center node.
- If the list has an even number of nodes, the middle is the **second** of the two center nodes (i.e., the ⌈n/2⌉-th node from the start, 1-indexed).

You should solve this in a single pass using only O(1) extra space.

## Function Signature

```text
(solve head)
```

- `head`: a list node (or `null` representing an empty list). Each node has integer `val` and reference `next`.
- Returns: the middle node.

## Input / Output Convention (Aura harness)

The harness reads **CASE0** lines from `stdin` (no prompts). Each case uses the format below; there may be multiple cases terminated by a line containing only `END`.

```
CASE0=<n>
<val_1>
<val_2>
...
<val_n>
```

- `<n>` = number of nodes in the linked list (`0 ≤ n ≤ 100000`).
- The next `<n>` lines each contain one integer — the value of each node in order from head to tail.
- If `n = 0`, the list is empty; the expected output is an empty line.
- For `n > 0`, the expected output is the value of the middle node on a single line.

Example:

```
CASE0=5
1
2
3
4
5
```

Expected output:

```
3
```

Example (even length):

```
CASE0=4
10
20
30
40
```

Expected output:

```
30
```

## Notes

- Use the slow/fast pointer technique: advance `slow` by one and `fast` by two each step; when `fast` reaches the end, `slow` is at the middle.
- Handle the empty list (`n = 0`) case by printing an empty line.
- Output only the middle node's value, one value per case.
