# Copy List with Random Pointer

## Problem

You are given a singly linked list where each node has two pointers:

- `next` — points to the next node in the list (or `null`).
- `random` — points to *any* node in the list (or `null`).

Each node also carries an integer value `val`.

Return the **head of a deep copy** of the list. The new list must contain entirely new node instances, but the structure must faithfully mirror the original: corresponding nodes in the copy should have their `next` and `random` pointers set to the **corresponding new nodes** (not the originals).

The original list must not be modified.

## Function Signature (Haskell)

```haskell
solve :: [NodeSpec] -> Int
-- returns the index of the head node of the constructed copy
```

`NodeSpec` describes one node in the original list as `(val, nextIndex, randomIndex)`, where indices refer to positions in the input list (`0`-based) and `-1` means `null`.

## Input Convention (stdin-less)

The test harness feeds the problem as `CASE0=...` lines on standard input. Each case lists the original list as a sequence of node specs, terminated by a sentinel.

Example:

```
CASE0=
N=5
NODES
10 -1 -1
20 0 2
30 1 -1
40 2 0
50 3 1
END
```

Where each `NODES` row is `val nextIdx randIdx` and `-1` means "no pointer".

## Output

Print the head index (0-based) of the newly constructed deep-copied list within your own node table.

## Notes

- The original list may be empty (`N=0`); in that case, output `-1`.
- `random` pointers can create cycles, point backward to earlier nodes, or be `null`.
- Do not reuse original node objects — allocate fresh nodes in your copy.
- A standard interleave-then-split approach runs in `O(n)` time and `O(1)` extra space (excluding the output nodes).
