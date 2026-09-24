# Flatten a Multilevel Doubly Linked List

## Problem

You are given a multilevel doubly linked list. In addition to the `next` and `prev` pointers that a standard doubly linked list has, each node also has a `child` pointer that may point to a separate, fully-formed doubly linked list. These child lists may themselves have nodes with their own `child` pointers, and so on, forming a tree-like structure on top of the underlying list.

Your task is to **flatten** the list so that all nodes appear in a single-level doubly linked list. The flattening must satisfy these rules:

1. Nodes are taken in **depth-first, preorder** order: visit a node, then recursively flatten its `child` sublist (if any) before moving to its `next` sibling.
2. After flattening, every node's `child` pointer must be set to `None`.
3. The `next` and `prev` pointers must form a single, valid doubly linked list spanning all nodes in the flattened order.

## Input

The input describes the multilevel list using a series of cases on stdin.

- `CASE0=n` — declares the start of case `n` (case index starts at 0).
- `NODE0=id type` — declares a node with the given integer id and type tag.
- `NEXT=from to` — sets `node[from].next = node[to]`.
- `PREV=from to` — sets `node[from].prev = node[to]`.
- `CHILD=from to` — sets `node[from].child = node[to]`.
- `IDLIST=id1 id2 ...` — declares the order of node ids in the flattened result for case `n`.

Node ids are integers that appear as the first field of a `NODE0=` declaration. Types are arbitrary short strings (e.g. `val`) and are ignored by the solver.

## Output

For each case, print one line containing the space-separated node ids in flattened, depth-first preorder order.

```
CASE0=0
NODE0=1 val
NODE0=2 val
NODE0=3 val
NODE0=4 val
NODE0=5 val
NODE0=6 val
NEXT=1 2
NEXT=2 3
NEXT=3 4
NEXT=4 5
NEXT=5 6
PREV=2 1
PREV=3 2
PREV=4 3
PREV=5 4
PREV=6 5
CHILD=3 7
NODE0=7 val
NEXT=7 8
NEXT=8 9
NEXT=9 10
PREV=8 7
PREV=9 8
PREV=10 9
CHILD=8 11
NODE0=11 val
NODE0=12 val
NEXT=11 12
PREV=12 11
IDLIST=
```

## Function Signature

```python
def solve(nodes: dict, child: dict) -> list[int]:
    """
    nodes[id] = {"next": id | None, "prev": id | None}
    child[id] = id | None   # head of the child sublist, or None
    """
```

## Notes

- The list is guaranteed to be well-formed: `next`/`prev`/`child` links only point to declared ids, and the structure is a multilevel doubly linked list with no cycles.
- Only the first node (the one with `prev is None`) participates in the final flattened output's `next` chain; orphan nodes reachable only through `child` must still be emitted in preorder, but their connections to siblings/cousins within their original sublist are irrelevant after flattening.
- You may assume there are at most a few thousand nodes per case.
