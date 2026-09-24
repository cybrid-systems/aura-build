# Longest Palindrome

## Problem

You are given a string consisting of letters (case-sensitive). You may rearrange the letters arbitrarily and use each character at most once. Determine the maximum possible length of a palindrome that can be formed.

Recall that a palindrome reads the same forwards and backwards. A palindrome of odd length has exactly one character appearing an odd number of times (its center); a palindrome of even length has every character appearing an even number of times.

## Function Signature

```python
def solve(s: str) -> int:
    ...
```

## Input / Output

The harness reads a single string `s` from the input.

- `CASE0=abccccdd`
- `CASE1=a`

For each case, output the length of the longest palindrome that can be built from the letters of `s`.

Expected outputs:
- `CASE0`: `7`  (e.g., `dccaccd`)
- `CASE1`: `1`

## Notes

- The letters are case-sensitive, so `'A'` and `'a'` are distinct.
- A single character is a palindrome of length 1.
