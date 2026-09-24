# First Letter to Appear Twice

## Problem

Given a string `s` consisting of lowercase English letters, return the **first letter** that appears **at least twice** in the string.

More precisely, let `i < j` be two indices such that `s[i] == s[j]`. Among all letters that occur at least twice, return the one whose **second** occurrence has the smallest index `j` (i.e., the earliest letter that completes a pair).

It is guaranteed that such a letter exists.

## Function Signature

```python
def solve(s: str) -> str:
    ...
```

## Input / Output

The harness drives the solution directly via the `solve` function (no stdin). Each test case is provided to `solve` as its argument, and the returned value is compared against the expected output.

**Test case format (illustrative):**

```
CASE0=s = "abccba"
CASE1=s = "abcdd"
CASE2=s = "abcdefghijklmnopqrstuvwxyzops"
```

Expected outputs (for reference):

- `CASE0` → `"c"` (positions 2 and 3)
- `CASE1` → `"d"` (positions 3 and 4)
- `CASE2` → `"o"`

## Notes

- A simple frequency table over the 26 lowercase letters is sufficient; track the index of each letter's second occurrence.
- The answer is unique because we look at the earliest *second* occurrence.
- The input string always contains at least one repeated letter.
