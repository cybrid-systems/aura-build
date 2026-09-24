# Count Vowel Substrings of a String

## Problem

A **vowel substring** is a contiguous substring of the given string that:

1. Contains **only** vowels (`a`, `e`, `i`, `o`, `u`, case-insensitive).
2. Has length **at least 2**.

Given a string `s`, count the number of vowel substrings it contains.

The same substring at different positions counts separately (e.g., in `"aba"`, the two substrings `"a"` at index 0 and index 2 each count only if length ≥ 2 — so length-1 substrings are ignored entirely).

## Function Signature

```python
def solve(s: str) -> int:
    ...
```

## Input

The harness drives `solve` with no stdin. Use the `CASE0` convention to set up the call:

```
CASE0=s="aeiou"
```

Multiple test cases are supported by stacking `CASE0=...`, `CASE1=...`, etc.

## Output

Your `solve` function must return a single integer: the number of vowel substrings of `s`.

## Examples

- `s = "aeiou"` → `10`
  (all substrings of length 2,3,4,5 — that is, C(5,2)+C(5,3)+C(5,4)+C(5,5) = 10)
- `s = "abc"` → `0`
  (no length-≥2 substring is composed entirely of vowels)
- `s = "aab"` → `1`
  (the substring `"aa"`)

## Notes

- Consider a sliding-window / two-pointer approach: for each left index, expand right while characters stay vowels, accumulating `right - left` for substrings ending at `right`.
- `1 ≤ len(s) ≤ 10^5` — an O(n) or O(n log n) solution is expected.
