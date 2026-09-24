# Replace the Substring for Balanced String

## Problem

You are given a string `s` consisting only of the characters `'Q'`, `'W'`, `'E'`, and `'R'`. The string is called **balanced** if each of the four characters appears exactly `n / 4` times, where `n = s.length`. Note that `n` is guaranteed to be a multiple of 4.

You may replace any contiguous substring of `s` with any string of the same length (containing only `'Q'`, `'W'`, `'E'`, `'R'`) in a single operation. Find the minimum length of a substring that needs to be replaced so that the resulting string is balanced.

## Function Signature

```python
def solve(s: str) -> int:
    ...
```

## Input/Output Convention

This problem uses the Aura harness format with no standard input. Read `s` from the variable `CASE0` (a single string). Write your answer to the variable `CASE1` as an integer, followed by `OK`.

Example harness lines:

```
CASE0=QWER
CASE1=0
OK
```

## Notes

- The minimum substring length can be 0, meaning the string is already balanced.
- Two substrings overlap only at contiguous ranges; merging consideration is handled implicitly by the sliding-window reduction.
- A two-pointer / sliding-window approach over `s` tracking the "excess" character counts outside the window runs efficiently in `O(n)` time.
