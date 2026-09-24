# Spiral Matrix II

## Problem

Given a positive integer `n`, construct an `n x n` matrix filled with the numbers `1` through `n^2` in spiral order, starting from the top-left corner and moving right, then down, then left, then up, repeating until all cells are filled.

Return the resulting matrix.

## Function Signature

```python
def solve(n: int) -> list[list[int]]:
    ...
```

## Input

A single line containing one integer `n` (`1 ≤ n ≤ 50`).

## Output

Print `n` lines, each containing `n` integers separated by spaces — the spiral matrix.

### Convention

For the Aura harness, parameters are supplied via `CASE0=` lines. A typical case looks like:

```
CASE0=n=3
```

`n` is extracted from this line and passed into `solve(n)`. The function's returned list-of-lists is printed row by row.

## Examples

### Example 1
Input:
```
3
```
Output:
```
1 2 3
8 9 4
7 6 5
```

### Example 2
Input:
```
1
```
Output:
```
1
```

### Example 3
Input:
```
4
```
Output:
```
1 2 3 4
12 13 14 5
11 16 15 6
10 9 8 7
```

## Notes

- The spiral traverses the outer layer first, then continues with the inner layer(s).
- Direction cycle: right → down → left → up → right → ...
- Edge cases to consider: `n = 1` (single cell) and odd `n` (the spiral converges to a single center cell that must receive the final value `n^2`).
