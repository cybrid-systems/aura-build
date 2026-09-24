# Find All Anagrams in a String

## Problem

Given a string `s` and a non-empty string `p`, find all starting indices in `s` where an anagram of `p` begins. An anagram means a substring of length `|p|` whose characters can be rearranged to form `p` (i.e., the two strings have identical character-frequency multisets).

Return every index `i` such that the substring `s[i : i + |p|]` is an anagram of `p`. The order of the returned indices does not matter.

## Function Signature

```python
def solve(s: str, p: str) -> list[int]:
    ...
```

## Input / Output Convention

This puzzle uses a **CASE0** stdin-less harness. The first line of the input section is the literal token `CASE0=...` containing the two strings in a fixed format. Decode the token to obtain `s` and `p`, then call `solve(s, p)` and print the resulting list of indices.

- Input line format: `CASE0=<s>|<p>` where `<s>` and `<p>` are the raw strings (with `|` chosen as the separator because it does not occur inside typical test strings).
- Output: a single line containing the space-separated indices, in ascending order. If no anagram exists, print an empty line.

### Example

```
CASE0=cbaebabacd|abc
```
Expected output (the substrings `"cba"` at index 0 and `"bac"` at index 6 are anagrams of `"abc"`):

```
0 6
```

## Notes

- A naive O(|s| · |p|) approach will be too slow for long inputs; aim for O(|s| + |p|) using a sliding window with character counts (a fixed-size alphabet of printable ASCII, lowercase letters, etc., depending on the test set).
- The window size is fixed at `|p|`. Slide it one character at a time, updating counts in O(1) per step, and record every position whose window counts match `p`'s counts.
- Return the indices sorted in ascending order; the natural left-to-right traversal already produces them in order.
