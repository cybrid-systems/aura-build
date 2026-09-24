# Binary Search Tree Iterator

## Problem

Implement an iterator over a binary search tree (BST). Your iterator must support two operations:

- `next()` — return the **next smallest** number in the BST.
- `has_next()` — return `true` if there are still smaller numbers remaining to visit, otherwise `false`.

The iterator is **initialized** with the root of a BST and must traverse the tree **without sorting all nodes at once**. Specifically, the memory used by the data structure backing the iterator must be bounded by **O(h)**, where *h* is the height of the tree.

## Function Signature

You will implement the following two functions (language-agnostic):

```
init(root) -> iterator   # called once with the BST root, before any queries
solve(it) -> answer      # repeated calls: returns next-smallest value, or a sentinel when exhausted
```

If your language uses explicit methods, the equivalent is:

```
def next(self) -> int:        # returns the next smallest value
def has_next(self) -> bool:   # returns True if more values remain
```

## Input / Output

The harness feeds a single test case using the following `CASE0=...` convention. There are no separate stdin streams; everything is encoded on the `CASE0=` lines.

A case value is one of two forms:

1. **Tree description** (only on the very first line of the case — establishes the BST and resets state):
   `CASE0=TREE:[v0,v1,v2,...]`
   The list is a level-order (breadth-first) representation of the BST. Use `null` (lowercase) for missing children. Example:
   `CASE0=TREE:[7,3,15,null,null,9,20]`
   builds:
   ```
            7
           / \
          3   15
             /  \
            9    20
   ```

2. **Query** (all subsequent lines in the case):
   `CASE0=OP:next`         → ask for the next-smallest value
   `CASE0=OP:has_next`     → ask whether more values remain
   `CASE0=OP:reset`        → reset the iterator back to the beginning (same tree)
   `CASE0=OP:end`          → terminate the case

For `OP:next`, the harness appends one output line per call, in the form:
`OUT=<value>`

For `OP:has_next`, the harness appends:
`OUT=true` or `OUT=false`

For `OP:reset` and `OP:end`, no output is produced.

A full example session:
```
CASE0=TREE:[7,3,15,null,null,9,20]
CASE0=OP:next
CASE0=OP:next
CASE0=OP:has_next
CASE0=OP:next
CASE0=OP:next
CASE0=OP:has_next
CASE0=OP:end
```
Expected outputs:
```
OUT=3
OUT=7
OUT=true
OUT=9
OUT=15
OUT=true
```

## Notes

- In-order traversal of a BST yields values in ascending order; use this property.
- A common solution maintains a stack of nodes representing the path to the current smallest unvisited node. Each `next()` operation is amortized **O(1)**, and the stack depth is **O(h)**.
- The BST contains **no duplicates**; node values are integers.
- `has_next()` must **not** advance the iterator; only `next()` does.
- A `reset` operation may be issued at any time and must restore the iterator to the state it had immediately after the initial `TREE:` line.
