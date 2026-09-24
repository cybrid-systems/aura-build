# Minimum Height Trees

## Problem

You are given a tree with `n` nodes labeled from `0` to `n - 1`, described by `n - 1` undirected edges. A **Minimum Height Tree (MHT)** is a rooted tree whose height (the number of edges on the longest root‑to‑leaf path) is as small as possible over all possible choices of root.

For the given tree, return **all** node labels that can serve as the root of a Minimum Height Tree. Return them in any order.

It is guaranteed that the input is a connected tree, so at least one MHT root exists.

## Function Signature

```clojure
(solve n edges)
```

- `n` — integer, the number of nodes (`1 ≤ n ≤ 10^4`).
- `edges` — vector of `[u v]` pairs (each `u`, `v` is an integer in `[0, n-1]`), the `n - 1` undirected edges of the tree.

Returns a vector of integer node labels — the roots of all Minimum Height Trees.

## Input / Output Convention (Aura harness)

The harness reads no stdin. Instead the function is invoked directly with the prepared arguments. The verification phase checks the returned vector:

```
CASE0_N=4
CASE0_EDGES=[[1,0],[1,2],[1,3]]
CASE0_EXPECTED=[1]
```

So for `n = 4` and edges `[[1,0],[1,2],[1,3]]` the answer is `[1]`.

A second illustrative case:

```
CASE1_N=6
CASE1_EDGES=[[0,3],[1,3],[2,3],[4,3],[5,4]]
CASE1_EXPECTED=[3,4]
```

## Notes

- For a single‑node tree (`n = 1`), the only root is `[0]`.
- An efficient approach repeatedly trims the current leaves (BFS/“peeling” from the outside in) until 1 or 2 nodes remain; those are exactly the MHT roots.
- The returned order of node labels does not matter.
- Complexity target: `O(n)` time and `O(n)` auxiliary space.
