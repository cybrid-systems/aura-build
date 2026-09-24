# Insertion Sort List

Sort a singly linked list using the **insertion sort** algorithm. The list is given as a vector of node values; reconstruct it as a linked list, sort it in place using insertion sort, then return the values of the sorted list from head to tail.

## Function signature

```lisp
(solve N VALUES)
```

- `N` — number of nodes (`1 ≤ N ≤ 2000`).
- `VALUES` — vector of `N` integers (each in the range `[-10^5, 10^5]`), representing the initial list from head to tail.

Return a vector containing the values of the sorted list, head to tail.

## I/O convention

Your solution is called from a stdin-less Aura harness. The harness invokes `(solve N VALUES)`. There is no `CASE0=` line because input is passed directly as Lisp values, not parsed from a string.

## Notes

- Insertion sort must be implemented explicitly on linked list nodes — do not simply call a built-in sort on the values and return them.
- A standard approach is to build the sorted portion one node at a time by inserting each new node into its correct position in the already-sorted prefix.
- The relative order of equal values must be preserved (stable).
- Time complexity target: `O(N^2)` is acceptable; optimizing to `O(N log N)` is not required.
