# Minimum Knight Moves

## Problem Statement

On an infinite chessboard, a knight starts at the origin `(0, 0)`. The knight moves in the standard L-shape: from any cell `(x, y)`, it can reach any of the eight positions `(x ± 1, y ± 2)` or `(x ± 2, y ± 1)`.

Given a target cell `(x, y)`, determine the **minimum number of knight moves** required to reach the target from the origin. The board is unbounded, so the knight is not constrained by any edges.

Your task is to compute this minimum move count for the given target.

## Function Signature

```clojure
(solve x y)
```

- `x` — the target x-coordinate (integer, possibly negative)
- `y` — the target y-coordinate (integer, possibly negative)
- Returns: the minimum number of knight moves from `(0, 0)` to `(x, y)` (integer)

## Input / Output Convention (stdin-less)

The harness feeds parameters via the function call `solve`. Each invocation corresponds to one test case. A typical driver emits results in the form:

```
CASE0=3
CASE1=0
CASE2=2
...
```

where each `CASEn=` line carries the answer for the *n*-th invocation of `solve`.

## Examples

| Target `(x, y)` | Minimum Moves |
|-----------------|---------------|
| `(0, 0)`        | `0`           |
| `(1, 1)`        | `2`           |
| `(2, 2)`        | `4`           |
| `(1, 0)`        | `3`           |
| `(2, 1)`        | `1`           |
| `(-1, -2)`      | `1`           |
| `(5, 5)`        | `4`           |

## Notes

- The board is **infinite**, so naive BFS over an enormous grid is impractical for large coordinates. Use symmetry and a bounded search region (or a known closed-form / DP approach) so the solution runs in reasonable time even for `|x|, |y|` up to ~10⁹.
- A natural symmetry to exploit: `solve(x, y) == solve(|x|, |y|)`.
- BFS from the origin will yield the correct shortest path, but be careful to cap the search window tightly to avoid memory blow-up on large inputs.
- `CASE0=` style output is produced by the harness; your function only needs to return the integer answer.
