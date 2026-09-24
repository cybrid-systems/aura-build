# Add Two Numbers II

## Statement

You are given two non-empty singly linked lists representing two non-negative integers. The digits of each integer are stored in **forward order** (most significant digit first), and each node holds a single digit (0-9). Add the two numbers and return the sum as a new linked list in the same forward order, without modifying the input lists.

Assume the input integers do not have leading zeros, except the number `0` itself, which is represented as a single node with value `0`.

## Function Signature

```clojure
(solve a b)
```

- `a`, `b`: the heads of two input linked lists.
- Returns: the head of a new linked list representing `a + b` in forward order.

## Input / Output Convention

Nodes are provided as Clojure vectors `[v1 v2 ... vn]` where `v1` is the head and `vn` is the tail. The harness will feed these into `solve` and render the returned vector.

Examples (informational only — the harness uses its own cases):

```
CASE0=(add [7 2 4] [5 6]) -> [1 0 1 7]      ;; 724 + 56  = 780 (not used by harness directly)
CASE1=(add [2 4 3] [5 6 4]) -> [8 0 7]      ;; 243 + 564 = 807
CASE2=(add [0] [0])          -> [0]
CASE3=(add [9 9] [1])        -> [1 0 0]     ;; 99 + 1 = 100
```

## Notes

- Do not mutate the input lists; you must read from them and produce a fresh list.
- Match the digit orientation: the units digit sits at the **last** node, so adding must proceed from the tail end — stack-based or reverse-walk approaches are natural.
- Do not strip a leading zero unless the resulting value is genuinely `0`; a result like `100` must be `[1 0 0]`, not `[1 0]`.
- Handle list-length differences cleanly; they need not be equal.
