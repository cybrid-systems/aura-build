# N-Queens II

## Problem Statement

The **n-queens puzzle** asks you to place `n` queens on an `n × n` chessboard such that **no two queens attack each other**. Two queens attack each other if they share the same row, column, or diagonal.

Given an integer `n`, return the **number of distinct solutions** to the n-queens puzzle. You do not need to construct the board configurations — only count them.

### Example

For `n = 4`, there are exactly **2** distinct solutions:

```
. Q . .     . . Q .
. . . Q     Q . . .
Q . . .     . . . Q
. . Q .     . Q . .
```

For `n = 1`, the answer is **1** (trivial placement).

For `n = 8`, the classical result is **92**.

## Function Signature

```clojure
(defn solve [n] ...)
```

- **Input:** `n` — an integer in the range `[1, 14]` (inclusive). For larger `n`, results grow large and time-to-solution becomes impractical with naive backtracking.
- **Output:** an integer — the total number of valid n-queens placements.

## Input Convention (Aura harness)

The harness feeds your solution via stdin in the following line format. Your program should read until EOF, parse each `CASE0=...` line, and print the result for each case on its own line in the same order.

```
CASE0=4
CASE0=1
CASE0=8
```

Expected stdout:

```
2
1
92
```

If multiple cases are present, output one answer per line, matching the order of the `CASE0=` lines.

## Notes

- **Backtracking with bitmasks** is the standard approach: track occupied columns and the two diagonal sets per row, pruning aggressively. Bitmask techniques (the classic "bitwise N-Queens") can comfortably handle `n` up to ~14.
- A pure recursive backtracking with three boolean arrays (columns, diag1, diag2) of length `n` is also sufficient for the given constraints.
- The result for `n ≥ 14` exceeds 32-bit integer range when using Java/Clojure boxed integers — consider using `long` or `Long` to be safe, though for the stated range `int` is fine.
- Each row must contain **exactly one** queen, so you only need to decide *which column* per row, giving a search space of `n!` in the worst case before pruning.
