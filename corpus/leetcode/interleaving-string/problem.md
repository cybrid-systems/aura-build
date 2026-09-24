# Interleaving String

## Problem

Given three strings `s1`, `s2`, and `s3`, determine whether `s3` can be formed by **interleaving** `s1` and `s2`.

An interleaving of two strings `s` and `t` is a configuration where `s` and `t` are split into some number of substrings (possibly zero), and these substrings are then concatenated in order. Equivalently, `s3` is an interleaving of `s1` and `s2` if there exists a way to walk through `s3` from left to right, consuming each character either from `s1` or from `s2`, such that the relative order of characters within each original string is preserved.

Return `true` if `s3` is an interleaving of `s1` and `s2`, otherwise return `false`.

## Function Signature

```python
def solve(s1: str, s2: str, s3: str) -> bool:
    ...
```

## Input / Output Convention

The harness drives I/O through `CASE0=...` lines on a single block of input. Each case begins with a line of the form:

```
CASE0=<bool>
```

followed by exactly three lines containing the strings `s1`, `s2`, and `s3`. The expected output for each case is the boolean result printed as `true` or `false` on its own line.

Example:

```
CASE0=true
aabcc
dbbca
aadbbcbcac
CASE1=false
aabcc
dbbca
aadbbbaccc
```

Expected output:

```
true
false
```

## Notes

- An early check that `len(s1) + len(s2) == len(s3)` is necessary — if it fails, no interleaving is possible.
- A 2D dynamic programming table where `dp[i][j]` indicates whether `s3[:i+j]` can be formed from `s1[:i]` and `s2[:j]` runs in `O(|s1| * |s2|)` time and `O(min(|s1|, |s2|))` space if optimized row-by-row.
