# Snakes and Ladders

## Problem

You are given an `n x n` board (1-indexed) for a game of Snakes and Ladders. Each square `i` (1 ≤ i ≤ n²) may contain:

- `-1`: no snake or ladder (default)
- a positive integer `j`: the destination square after landing on `i` (either a snake head/bottom or a ladder top)

You start on square `1` and want to reach square `n²`. On each move, you roll a 6-sided die and move forward by the rolled value `k`. You must stay within the board (`i + k ≤ n²`). If the destination square has a snake or ladder, you are immediately transported to that square's value.

Find the **minimum number of moves** required to reach square `n²`. If it is impossible, return `-1`.

## Function Signature

```python
def solve(board: list[list[int]]) -> int:
    pass
```

The `board` is provided as a flat representation per the input format below.

## Input

A single test case is read from standard input in this form:

```
CASE0=<n>
<row 0 of board, space-separated>
<row 1 of board, space-separated>
...
<row n-1 of board, space-separated>
```

Where `-1` denotes an empty square and a positive integer denotes a snake or ladder destination. Square numbering follows the standard boustrophedon (left-to-right on row 0, right-to-left on row 1, etc.), starting at 1 in the bottom-left.

## Output

A single line with the minimum number of moves, or `-1` if unreachable.

## Notes

- The board size `n` is between 2 and 20.
- A snake/ladder entry is never `-1` and never points to itself.
- BFS over squares (treating each square as a node and dice rolls as edges) yields the optimal answer.
- Remember to apply snake/ladder teleportation **after** each dice roll, before recording the visited square.
