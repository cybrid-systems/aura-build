# Walls and Gates

You are given an `m × n` grid where each cell contains one of three values:

- `-1` — a wall or obstacle
- `0`  — a gate
- `INF` — an empty room (represented as `2147483647`)

For every empty room, replace its value with the **distance** (number of steps, i.e., cells in a 4-connected path through empty rooms and gates) to its nearest gate. Walls stay `-1` and gates stay `0`. If a room cannot reach any gate, leave it as `INF`.

The grid size satisfies `m, n ≥ 1` and `m · n ≤ 10⁶`.

## Function Signature

Implement a function with the following shape so the harness can call it directly:

```text
solve(grid: list[list[int]]) -> None
```

The function mutates `grid` in place and returns nothing.

## Input

The harness streams a **single test case** on stdin in the following format:

```
CASE0=<m>
<n rows of <n> space-separated integers each>
```

Example:

```
CASE0=3
-1 0 INF
INF INF INF
0 INF -1
```

Read `m`, then read `m` rows of `n` integers each, build the grid, and call `solve`.

## Output

After `solve` returns, the harness writes the mutated grid back to stdout, one row per line, with values space-separated.

Using the example above, the expected output is:

```
-1 0 3
2 2 1
0 1 -1
```

## Notes

- Start BFS from **all gates simultaneously** (multi-source BFS) for an O(m·n) solution.
- Walls (`-1`) are not traversable, but movement is otherwise 4-directional (up, down, left, right) through any non-wall cell.
- The harness guarantees `m · n ≤ 10⁶`, so an explicit queue with O(1) push/pop is recommended.
