# Valid Sudoku

## Problem

You are given a 9×9 Sudoku board represented as a list of lists of characters `board`, where each cell contains a digit `'1'`–`'9'` or `'.'` (an empty cell). Determine whether the board is **valid** — that is, whether every filled cell satisfies the Sudoku constraints:

- Each **row** contains no repeated digits.
- Each **column** contains no repeated digits.
- Each of the nine **3×3 sub-boxes** (top-left corners at rows/columns `(0,0), (0,3), (0,6), (3,0), (3,3), (3,6), (6,0), (6,3), (6,6)`) contains no repeated digits.

You only need to verify that no rule is currently broken; you do **not** need to solve the board.

Write a function `solve(board)` that returns `True` if the board is valid, and `False` otherwise.

## Function Signature

```python
def solve(board: list[list[str]]) -> bool:
    ...
```

## Input

The board is provided directly as a Python `list[list[str]]` (no stdin). For convenience, test cases use the `CASE0=` form:

```
CASE0=[["5","3",".",".","7",".",".",".","."],["6",".",".","1","9","5",".",".","."],[".","9","8",".",".",".",".","6","."],["8",".",".",".","6",".",".",".","3"],["4",".",".","8",".","3",".",".","1"],["7",".",".",".","2",".",".",".","6"],[".","6",".",".",".",".","2","8","."],[".",".",".","4","1","9",".",".","5"],[".",".",".",".","8",".",".","7","9"]]
ANSWER0=True
```

## Output

Return `True` if the board satisfies all Sudoku constraints, otherwise return `False`.

## Notes

- Empty cells are denoted by the character `'.'` and should be ignored during validation.
- The board is always 9×9.
- A hash‑set (or bitset) per row/column/box keeps the solution **O(81)** time and **O(1)** extra space (the 27 sets hold at most 9 elements each).
- Do not mutate the input board.
