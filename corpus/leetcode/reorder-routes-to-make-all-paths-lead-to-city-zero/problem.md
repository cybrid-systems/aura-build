# Reorder Routes to Make All Paths Lead to the City Zero

## Statement

There are `n` cities numbered from `0` to `n-1`, connected by `n-1` directed roads forming a tree rooted at city `0`. Each road is given as a pair `[u, v]` meaning the current direction allows travel **from `u` to `v`**.

You may *reverse* any road, at unit cost per reversal. After performing any number of reversals, every city (other than `0` itself) must be able to reach city `0` by following the directed roads. Return the **minimum number of reversals** required.

## Function Signature

```python
def solve(n: int, connections: list[list[int]]) -> int:
    ...
```

- `n`: the number of cities (1 ≤ n ≤ 2·10⁵).
- `connections`: list of `n-1` directed edges `[u, v]`, each road appearing exactly once.

## Input / Output Convention (Aura harness)

The harness calls `solve(n, connections)` directly — there is no stdin. For local testing, an equivalent `CASE0` style file would look like:

```
CASE0
n = 5
connections = [[1,0],[1,2],[2,3],[4,2]]
ANS = 2
CASE1
n = 4
connections = [[1,0],[2,0],[3,2]]
ANS = 0
```

- `CASE0`: 1 line listing the expected return value of `solve(n, connections)`.
- Subsequent cases follow the same format, separated by blank lines.

## Notes

- The underlying graph is a tree, so BFS/DFS from city `0` along the undirected skeleton visits every city exactly once.
- During the traversal, count only edges whose current direction points **away** from `0` (i.e., `u → v` where `u` is the side already reached). Each such edge must be reversed.
- The graph is guaranteed to be a valid tree; no disconnected or cyclic cases occur.
- Aim for `O(n)` time and `O(n)` memory to handle the upper bound comfortably.
