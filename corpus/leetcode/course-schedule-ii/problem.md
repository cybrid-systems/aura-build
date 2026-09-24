# Course Schedule II

## Problem Statement

You are given `n` courses labeled from `0` to `n-1` and a list of prerequisite pairs where each pair `[a, b]` indicates that course `a` must be taken before course `b`. Some courses may have no prerequisites, while others may have multiple.

Return **any** valid ordering of all `n` courses such that every course appears exactly once and every prerequisite constraint is satisfied. If no such ordering exists (i.e., the prerequisite graph contains a cycle), return an empty array.

## Function Signature

```python
def solve(n: int, prerequisites: list[list[int]]) -> list[int]:
```

**Parameters**
- `n`: the total number of courses (`0 <= n <= 10^4`).
- `prerequisites`: a list of pairs `[a, b]` meaning `a` must come before `b`.

**Returns**
- A list of `n` course IDs forming a valid topological ordering, or `[]` if impossible.

## Input / Output Convention (Aura Harness)

The harness drives I/O line-by-line in the following form. Your `solve` function will be called per test case.

```
CASE0=2
n=4
prerequisites=[[1,0],[2,0],[3,1],[3,2]]
expected=[0,1,2,3]
```

- `CASE0=<id>` — case identifier (ignored by the solver).
- `n=<int>` — number of courses.
- `prerequisites=<python-literal-list>` — the prerequisite pairs.
- `expected=<python-literal>` — the expected ordering (informational; any valid ordering is accepted).

Output is produced by the harness from `solve`'s return value.

## Notes

- Multiple valid orderings may exist; return any one of them.
- If `n == 0`, return `[]`. If no topological ordering exists (cycle detected), return `[]`.
- A standard Kahn's algorithm (BFS with in-degree tracking) or DFS-based topological sort is sufficient within the time limits.
