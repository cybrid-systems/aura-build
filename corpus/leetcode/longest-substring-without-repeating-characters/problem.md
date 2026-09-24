# Longest Substring Without Repeating Characters

## Problem

Given a string `s`, find the length of the longest substring that contains no repeating characters.

A *substring* is a contiguous sequence of characters within the string. For example, the substrings of `"abc"` are `"a"`, `"b"`, `"c"`, `"ab"`, `"bc"`, and `"abc"`.

Your task is to return the maximum length of any substring of `s` such that every character within that substring appears only once.

## Function Signature

```python
def solve(s: str) -> int:
    ...
```

## Input

A single line containing the string `s`.

- `s` consists of printable ASCII characters (letters, digits, punctuation, spaces, etc.).
- `0 <= len(s) <= 10^5`

## Output

A single integer: the length of the longest substring without repeating characters.

If `s` is empty, output `0`.

## Examples

### Example 1
```
CASE0=abcabcbb
```
Output:
```
3
```
Explanation: The answer is `"abc"`, with length `3`.

### Example 2
```
CASE0=bbbbb
```
Output:
```
1
```
Explanation: Every substring longer than `1` contains repeated characters.

### Example 3
```
CASE0=pwwkew
```
Output:
```
3
```
Explanation: The answer is `"wke"`, with length `3`. Note that `"pwke"` is a subsequence, not a substring.

### Example 4
```
CASE0=
```
Output:
```
0
```
Explanation: The empty string has no non-empty substrings.

## Notes

- A standard sliding-window approach using a hash map of last-seen positions runs in `O(n)` time and `O(k)` space, where `k` is the size of the character alphabet.
- Be careful: when a repeated character is encountered, the window's left boundary should move to one past the previous occurrence — not just forward by one — to maintain the no-repeat invariant.
