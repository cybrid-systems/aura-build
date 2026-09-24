# Flood Fill

## Problem

You are given a 2D screen represented as an array of `m` rows and `n` columns, where each cell holds an integer color. An image is "flood filled" by recoloring every cell in the **4-connected** component (up, down, left, right — no diagonals) that contains the starting pixel `(sr, sc)`, provided that the cell's current color equals the original color of the starting pixel.

Given the screen, a starting position, and a new color, return the screen after performing the flood fill.

## Function Signature

```python
def solve(screen: list[list[int]], sr: int, sc: int, new_color: int) -> list[list[int]]:
```

**Parameters**
- `screen`: a list of `m` lists, each containing `n` integers representing pixel colors. `1 <= m, n <= 50`.
- `sr`, `sc`: zero-based coordinates of the starting pixel. `0 <= sr < m`, `0 <= sc < n`.
- `new_color`: the integer color to apply. `0 <= new_color <= 10^4`.

**Returns**
- The modified `screen` (the same 2D list mutated, or a new list) after the flood fill.

## Input / Output Convention

The harness drives I/O through labeled `CASE` lines on stdin — but this puzzle exposes **no stdin**; the `solve` function is called directly by the harness with the arguments above.

Example of the conventional harness trace (illustrative only):

```
CASE0=screen=[[1,1,1],[1,1,0],[1,0,1]], sr=1, sc=1, new_color=2
CASE0.expected=[[2,2,2],[2,2,0],[2,0,1]]
```

## Notes

- Only cells whose original color matches `screen[sr][sc]` are recolored; cells of any other color are left untouched, even if they are adjacent.
- If `new_color` already equals the starting pixel's color, the screen is returned unchanged (the component is still "visited" but no visible changes occur).
- Use BFS or DFS — both are acceptable; recursion depth is bounded by `m * n <= 2500`.
