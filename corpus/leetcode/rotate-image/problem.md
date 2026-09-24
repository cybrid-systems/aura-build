# Rotate Image

## Problem

You are given an `n × n` 2D matrix of integers. Rotate the matrix by **90 degrees clockwise**, **in-place** (i.e., without allocating another `n × n` matrix).

After rotation, the element that was originally at position `(row, col)` should end up at position `(col, n - 1 - row)`.

## Function Signature

```
def solve(matrix: list[list[int]]) -> list[list[int]]
```

- `matrix`: an `n × n` list of lists of integers, with `n` in the range `[1, 200]` and values in the range `[-1000, 1000]`.
- **Returns**: the same matrix object, rotated in-place. (Returning the rotated matrix is also accepted for convenience.)

## Input / Output

This problem uses a stdin-less harness. Each case is encoded as a `CASE0=...` line that the harness decodes into the argument of `solve`.

- `CASE0=[[1,2,3],[4,5,6],[7,8,9]]` → expected output `[[7,4,1],[8,5,2],[9,6,3]]`
- `CASE0=[[1,2],[3,4]]` → expected output `[[3,1],[4,2]]`
- `CASE0=[[1]]` → expected output `[[1]]`

The harness will pass the decoded Python list as the `matrix` argument to your `solve` function and compare the return value against the expected result.

## Notes

- Modifying the matrix in-place is required by the problem; returning a freshly allocated `n × n` matrix is not considered a valid solution.
- A common approach is the "transpose then reverse each row" trick, but any in-place 90° clockwise rotation that runs in `O(n²)` time is acceptable.
- Be careful with even/odd `n`: the layer-by-layer swap method must handle the center cell of odd-sized matrices correctly (it should stay in place).
