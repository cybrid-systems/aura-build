# Dungeon Game

The demons had captured the princess. She is being held in the bottom-right corner of an `m × n` dungeon, while the knight starts at the top-left cell. Our knight must rescue the princess, moving only **right** or **down** at each step.

Each cell of the dungeon contains a number:
- A **negative** value means the knight loses that many health points entering the cell.
- A **positive** value (or `0`) means the knight gains that many health points entering the cell.

The knight's health can never drop to `0` or below — at any moment, health must remain **strictly positive** (i.e., at least `1`). If his health would drop to `0` or below when entering a cell, he dies immediately.

Determine the **minimum initial health** the knight needs at the top-left cell so that he can guarantee reaching the princess in the bottom-right cell.

## Function Signature

```haskell
solve :: [[Int]] -> Int
```

## Input

The dungeon grid is given as a list of lists on a single line:

```
CASE0=[[ -2, -3,  3],
       [ -5,-10,  1],
       [10, 30, -5]]
```

- The first token `CASE0=` is a literal prefix (ignore it).
- The remaining tokens form a rectangular matrix of integers.

## Output

A single integer — the minimum initial health required.

```
ANS=7
```

## Notes

- The knight starts **before** entering cell `(0,0)`, so any loss/gain from that cell still applies.
- Health after each step must remain `≥ 1`.
- The answer is unique and always fits in a standard 32-bit signed integer.
