# Wildcard Matching

## Problem

Implement wildcard pattern matching with support for the special characters `'?'` and `'*'`.

- `'?'` matches any **single** character.
- `'*'` matches any **sequence of characters**, including the empty sequence.
- All other characters match themselves exactly (case-sensitive).

Given a string `s` (length `n`) and a pattern `p` (length `m`), determine whether `p` matches the **entire** string `s`.

## Function Signature

```python
def solve(s: str, p: str) -> bool:
    ...
```

## Input / Output Convention

Input is provided by the harness on standard input, one test case per scenario.

- The first line contains an integer `T` — the number of test cases.
- Each test case consists of two lines:
  - Line 1: the string `s`.
  - Line 2: the pattern `p`.

Output: for each test case, print `1` if the pattern matches the string, otherwise `0`. Each result on its own line.

### Example

Input:
```
4
aa
a
aa
*
cb
?a
cb
?a*
```

Output:
```
0
1
0
1
```

## Notes

- `1 <= n, m <= 2000`. An `O(n*m)` DP with careful pruning is acceptable; an `O(n*m)` solution that uses `O(min(n,m))` extra memory is also feasible.
- The empty pattern matches only the empty string, and `'*'` alone matches any string.
- This is the classic *full match* problem: the pattern must consume the entire input; partial matches do not count.
- Your `solve` function should treat `s` and `p` as given and return a boolean; the harness handles I/O.
