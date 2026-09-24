# Longest Repeating Character Replacement

## Problem

Given a string `s` consisting of uppercase English letters and an integer `k`, you may perform **at most `k`** replacement operations on the string. Each operation lets you pick any character in the string and change it to any other uppercase English letter.

Find the length of the longest substring you can obtain such that **all characters in the substring are identical** after at most `k` replacements.

## Function Signature

```python
def solve(s: str, k: int) -> int:
    ...
```

## Input / Output Convention

A single test case is provided via the harness using the standard `CASE0=...` convention. For example:

```
CASE0=s="AABABBA"
CASE0=k=1
```

The function `solve(s, k)` should return the length of the longest valid substring as an `int`.

## Notes

- A classic sliding-window approach maintains counts of characters in the current window. The window is valid when `window_length - max_frequency_in_window <= k`.
- The answer for `s = "AABABBA"`, `k = 1` is `4` (e.g., replace one `A` in `"AABB"` or one `B` in `"ABBA"`).
- `0 <= len(s) <= 10^5` and `0 <= k <= len(s)`.
