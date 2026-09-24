# Zigzag Conversion

## Problem

Write the characters of a string `s` into a zigzag pattern that flows down across `numRows` rows, then read the rows from top to bottom to form a new string.

The pattern is built by writing the first row's first character, then moving down one row at a time until reaching the last row. From the last row, move diagonally up-and-to-the-right (skipping every row in between) until you return to the first row, then move down again, and repeat until all characters are placed.

For example, with `s = "PAYPALISHIRING"` and `numRows = 3`:

```
P   A   H   N
A P L S I I G
Y   I   R
```

Reading row by row gives `"PAHNAPLSIIGYIR"`.

For `numRows = 4`:

```
P     I     N
A   L S   I G
Y A   H R
P     I
```

Reading row by row gives `"PINALSIGYAHRPI"`.

Given `s` and `numRows`, return the resulting string.

## Function Signature

```
(solve s numRows)
```

## Input

The input is read line-by-line from `INPUT_FILE`. Each case begins with a line containing `numRows` followed by the string `s` on the same line (or on a separate line that immediately follows). A blank line or end-of-file separates cases. Each test case is independent.

Example input (CASE0):

```
numRows=3 s=PAYPALISHIRING
```

## Output

For each case, print the zigzag conversion of `s` on its own line.

Example (CASE0):

```
PAHNAPLSIIGYIR
```

## Notes

- `numRows = 1` is a special case: the answer equals `s`.
- When `numRows >= len(s)`, the answer also equals `s`.
- A single-traversal solution that appends characters to per-row buffers (or computes indices directly) runs in `O(n)` time.
