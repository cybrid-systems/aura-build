# Implement strStr()

## Problem Statement

Implement `strStr(haystack, needle)` that returns the index of the first occurrence of `needle` in `haystack`, or `-1` if `needle` is not a substring of `haystack`.

Clarifications:
- Return `0` when `needle` is the empty string.
- `needle` is guaranteed to be shorter than or equal to `haystack` in length when non-empty.

## Function Signature

```python
def solve(haystack: str, needle: str) -> int:
    ...
```

## Input / Output Convention

Input is read **line by line** from standard input. Each test case consists of two lines:
- Line 1: the `haystack` string
- Line 2: the `needle` string

A line containing the single character `#` (with nothing else on it) terminates input.

For each test case, output a single line containing the integer answer.

Example input (`CASE0` style header lines are **not** used; the harness reads raw lines):

```
hello
ll
aaaaa
bba
abc
a
#
```

Example output:

```
2
-1
0
```

## Notes

- The test cases are given one pair per group; the only terminator is the line `#`.
- Strip each line of trailing newlines before processing; do not strip internal whitespace (none is expected in this problem).
