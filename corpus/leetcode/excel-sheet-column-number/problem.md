# Excel Sheet Column Number

## Problem

Given a string `s` representing a column title as it appears in an Excel spreadsheet, return the corresponding column number.

Excel columns are labeled using a base-26 (bijective) system:

- `A` → 1
- `B` → 2
- ...
- `Z` → 26
- `AA` → 27
- `AB` → 28
- ...
- `ZY` → 701
- `ZZ` → 702
- `AAA` → 703
- ...

In other words, each letter acts like a digit where `'A'` is the digit `1` (not `0`), and there is no zero digit — values `1..26` map to `A..Z`, then `27` is `AA`, etc.

## Function Signature

```lisp
(defun solve (s) ...)
```

`S` is a non-empty uppercase string of letters `A..Z`. Return the column number as an integer.

## Input / Output Convention

Input is provided via standard `CASE0=` / `CASE0=` lines on stdin (handled by the harness), one per test case:

```
CASE0=AB
CASE0=Z
CASE0=AA
```

For each `CASE0=<s>`, print the corresponding column number on its own line.

### Examples

| Input    | Output |
|----------|--------|
| `A`      | `1`    |
| `Z`      | `26`   |
| `AA`     | `27`   |
| `AB`     | `28`   |
| `AZ`     | `52`   |
| `BA`     | `53`   |
| `ZZ`     | `702`  |
| `AAA`    | `703`  |

## Notes

- Treat the string as base-26 with digit values `1..26`; the rightmost letter is the least significant digit.
- The answer always fits comfortably in a 32-bit signed integer for the given constraints, but use 64-bit (or bignum) arithmetic to be safe for arbitrary lengths.
- An iterative left-to-right accumulation `ans = ans * 26 + (c - 'A' + 1)` is the natural approach.
