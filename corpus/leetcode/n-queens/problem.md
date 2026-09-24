# N-Queens

## Problem

The *n*-queens puzzle is the problem of placing `n` queens on an `n × n` chessboard such that no two queens attack each other.

Given an integer `n`, return all distinct board configurations where this holds. Each configuration is represented as a list of `n` strings of length `n`, where `'Q'` marks a queen and `'.'` marks an empty cell (one string per board row). The order of configurations in the result does not matter.

### Example

For `n = 4`, one valid configuration is:

```
. Q . .
. . . Q
Q . . .
. . Q .
```

All such configurations for `n = 4` should appear in the output.

## Function Signature

```python
def solve(n: int) -> list[list[str]]:
    ...
```

## Input / Output Convention

The harness invokes `solve(n)` directly with a single integer `n` (no stdin is read). To make manual debugging easy, a driver also prints the count and the first configuration using this format:

```
CASE0=n
ANS0c=<number of solutions>
ANS0_0=<first configuration as a single line with rows concatenated, using '.' and 'Q'>
```

For example, when `n = 4`:

```
CASE0=4
ANS0c=2
ANS0_0=.Q....QQ...Q.....QQ..
```

(Each row of the first solution is concatenated; rows of subsequent solutions, if any, follow in order: `ANS0_1`, `ANS0_2`, …)

## Notes

- `n` may be as small as `1`. For `n = 1` there is exactly one solution.
- For larger `n` the number of solutions can grow quickly, but is finite for every `n`.
- Queens attack along rows, columns, and both diagonals; ensure all three are unconstrained within each solution.
