# Course Schedule

## Problem

There are `N` courses labeled `0` to `N-1`. You are given `M` prerequisite pairs where each pair `[a, b]` means you must take course `b` before course `a` (i.e., there is a directed edge `b → a`). Determine whether it is possible to finish all courses, or if some prerequisite cycle makes it impossible.

Return `true` if all courses can be completed, otherwise `false`.

## Input

The input is read line by line from standard input, but for this harness the entire input is provided as a single string via the `CASE0` environment-style line below. Your function will receive the parsed values directly.

```
CASE0=N=2, PREREQS=[[1,0]]
```

- `N` — integer, the number of courses.
- `PREREQS` — JSON array of `[a, b]` pairs (integers), meaning edge `b → a`.

You may assume `0 ≤ a, b < N` and `0 ≤ M ≤ N*(N-1)/2`.

## Output

Write the result to standard output as a single line:

```
true
```

or:

```
false
```

## Function Signature

```python
def solve(N: int, prereqs: list[list[int]]) -> bool:
    ...
```

## Example

Input:
```
CASE0=N=2, PREREQS=[[1,0]]
```
Interpretation: take course `0` before course `1`. No cycle exists.

Output:
```
true
```

## Example

Input:
```
CASE0=N=2, PREREQS=[[1,0],[0,1]]
```
Interpretation: cycle `0 → 1 → 0`. Impossible to finish both.

Output:
```
false
```

## Notes

- An empty `PREREQS` list trivially yields `true` (no constraints).
- Both DFS-based cycle detection (with three-color marking) and Kahn's BFS topological sort (count visited nodes vs `N`) are acceptable approaches.
- `N` can be up to `10^5`, so build an adjacency list and run in `O(N + M)` time.
