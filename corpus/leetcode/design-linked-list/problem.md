# Design Linked List

## Problem Statement

Design and implement a **singly linked list** data structure that supports the following operations:

- `get(index)` — Return the value of the **index**-th node in the linked list (0-indexed). If the index is out of range, return `-1`.
- `addAtHead(val)` — Prepend a node of value `val` to the beginning of the linked list.
- `addAtTail(val)` — Append a node of value `val` to the end of the linked list.
- `addAtIndex(index, val)` — Insert a new node of value `val` **before** the **index**-th node. If `index` equals the length of the linked list, the node is appended to the end. If `index` is greater than the length, the node will not be inserted.
- `deleteAtIndex(index)` — Delete the **index**-th node if the index is valid.

Implement a class `MyLinkedList` with these methods. The linked list is initially empty.

## Function Signature

```clojure
(solve [n ops]
  ;; ops is a sequence of operation vectors
  ;; return a sequence of results for query operations)
```

## I/O Convention

The harness invokes `solve` with two arguments: `n` (the number of operations) and `ops` (a vector of operation vectors). Each operation follows one of these shapes:

```
CASE0=n
CASE0_0=["MyLinkedList","addAtHead","addAtTail","addAtIndex","get","deleteAtIndex","get"]
CASE0_1=[[], [1], [3], [1,2], [1], [1], [1]]
CASE0_2=[null, null, null, null, 2, null, 3]
```

For each operation in order:
- The **first** operation is always `"MyLinkedList"` (the constructor); its result is `null` (omitted).
- Mutating operations (`addAtHead`, `addAtTail`, `addAtIndex`, `deleteAtIndex`) return `null` (omitted from the output).
- Query operations (`get`) return the corresponding integer (included in the output in order).

The output is a single line containing the query results, in order, space-separated.

## Notes

- Indexing is **0-based**.
- An out-of-bounds `get` or `deleteAtIndex` is a no-op for delete and returns `-1` for get.
- `addAtIndex` with `index < 0` is treated as inserting at the head; `index == length` appends; `index > length` is a no-op.
- Aim for **O(1)** for head operations and **O(index)** for indexed operations (which is acceptable for this problem).
