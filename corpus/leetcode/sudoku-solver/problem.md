# Sudoku Solver

## Problem

You are given a partially filled 9×9 Sudoku board. Your task is to fill the empty cells so that the final board satisfies the standard Sudoku rules:

- Each row contains every digit from `1` to `9` exactly once.
- Each column contains every digit from `1` to `9` exactly once.
- Each of the nine 3×3 sub-grids (boxes) contains every digit from `1` to `9` exactly once.

Empty cells on the input board are represented by `.` (a single dot). The input is guaranteed to have exactly one valid solution.

## Input

A single test case. The board is provided as 9 lines of 9 characters each.

```
CASE0=53..7....
CASE0=6..195...
CASE0=.98....6.
CASE0=8...6...3
CASE0=4..8.3..1
CASE0=7...2...6
CASE0=.6....28.
CASE0=...419..5
CASE0=....8..79
```

Each `CASE0=` line contributes 9 characters to the board, in order. The line after the prefix (without leading/trailing whitespace) is taken verbatim.

## Output

Print the solved 9×9 board as 9 lines of 9 digits, with no separator between rows. Follow the output with a single line containing `#`.

```
# sample output for the input above
534678912
672195348
198342567
859761423
426853791
713924856
961537284
287419635
345286179
#
```

## Function Signature

```haskell
solve :: String -> String
-- solve boardAs9Lines returns the solved board as 9 lines (with trailing newline)
```

Where `boardAs9Lines` is the 9 input lines concatenated (or passed in whatever string form your language's harness uses); see the I/O convention for exact framing.

## Notes

- The solver should run comfortably within the time limit using straightforward backtracking with bitmask-based candidate tracking (one 9-bit mask per row, column, and 3×3 box is typically enough).
- Guarantee of a unique solution means you may stop as soon as the board is filled; no need to enumerate alternatives.
- The trailing `#` marker is required so the judge can delimit multi-line output cleanly.
