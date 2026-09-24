# Redundant Connection

## Problem

You are given a graph that started as a tree with `n` labeled nodes (`1..n`) and then had **one** extra edge added to it. The extra edge created exactly one cycle.

Find any edge that can be removed so that the resulting graph is a tree (i.e., it becomes connected and acyclic). If multiple answers exist, return the last one in the input.

## Input

The harness supplies pre-parsed input lines named `CASE0`..`CASE9`.

Each case contains:
- Line 1: two integers `n` and `e` (number of nodes, number of edges), where `e = n`.
- Lines 2..e+1: each has two integers `u` and `v` describing an undirected edge.

Output one edge `u v` that is redundant.

## Function Signature

```lisp
(defun solve (n edges)
  ;; edges: list of (u . v) pairs in input order
  ;; returns a list (u v) — the redundant edge
  )
```

## Output

For each `CASEi`, print one line:

```
CASEi=<u> <v>
```

where `<u> <v>` is the redundant edge (the last such edge in the input if there are ties).

## Notes

- The graph is undirected; an edge `(u, v)` connects both directions.
- `1 <= n <= 1000`, `e == n`.
- Two valid approaches: Union-Find (DSU) detecting the first edge that closes a cycle, or DFS that detects the back-edge on a cycle and returns its last-occurring input edge.
- Since the input is already pre-parsed by the harness, do not read from stdin; just consume the `CASE` parameters and call `solve`.
