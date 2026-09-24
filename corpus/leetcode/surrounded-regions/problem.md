# Surrounded Regions

## Problem

You are given an `m × n` board represented as a list of strings (rows) containing only the characters `'X'` and `'O'`. A region of `'O'` cells is **surrounded** if none of its cells touches the border of the board. Your task is to flip every `'O'` that belongs to a surrounded region into `'X'`. All other `'O'` cells (those connected to the border, even indirectly) must remain `'O'`.

Return the resulting board after performing the capture.

## Function Signature

```python
def solve(board: list[str]) -> list[str]:
    ...
```

## Input / Output Convention (stdin-less harness)

- The harness feeds the test case to your `solve` function directly via its parameter.
- `CASE0=board` lines in the harness driver are not used; parameters are passed positionally.
- Each row in `board` is a string of equal length containing only `'X'` or `'O'`.
- Return a new list of strings of the same shape.

### Examples

**Example 1**
```
Input board:
["XXXX",
 "XOOX",
 "XXOX",
 "XOXX"]

Output:
["XXXX",
 "XXXX",
 "XXXX",
 "XOXX"]
```
The central `O`s form a region not touching any border, so they are flipped.

**Example 2**
```
Input board:
["XXXX",
 "XOOX",
 "XOOX",
 "XOXX",
 "XOOXX".replace("XX", "X")]  # illustrative; not real input

```
Any `O` connected to the border (top, bottom, left, or right edge) survives.

## Notes

- The classic approach runs BFS/DFS from every border `'O'`, marking those cells as **safe**. After scanning all borders, every still-unmarked `'O'` is flipped to `'X'`.
- Modifying the input in place is acceptable as long as the returned board reflects the final state; if you mutate, remember that rows are immutable strings — convert to a list of lists first, or build a fresh result.
- Time complexity: `O(m · n)` with `O(m · n)` extra space for the visited/safe marks (or use the board itself with a sentinel character).
- Empty boards and `1 × 1` boards must be handled (no `'O'` is surrounded in a single-cell board since it touches the border).
