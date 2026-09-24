# Minimum Window Subsequence

## Problem

You are given two strings `S` and `T`. Find the minimum-length contiguous substring of `S` such that `T` is a subsequence of that substring. If no such substring exists, return the empty string. If multiple substrings of the same minimum length exist, return the one that appears earliest in `S`.

A subsequence is formed by deleting zero or more characters without reordering the remaining ones.

## Function Signature

```python
def solve(s: str, t: str) -> str:
    ...
```

## Input / Output Convention

`CASE0` contains the two strings `S` and `T` separated by a space on a single line:

```
CASE0=abacbabc T=abcabc
```

The output line must be of the form:

```
ANS0=<answer>
```

where `<answer>` is the minimum-window substring, or an empty string if none exists.

## Notes

- `1 <= |S|, |T| <= 1000`
- `T` must appear as a subsequence of `S` for an answer to exist; otherwise output `""`.
- Among all valid substrings, choose the shortest; break ties by leftmost (earliest) starting index in `S`.
- The answer is guaranteed (when non-empty) to include `T` in order but does not need to start or end with characters of `T`.
