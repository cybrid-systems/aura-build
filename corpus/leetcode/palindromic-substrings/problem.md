# Palindromic Substrings

## Problem

A **palindrome** is a string that reads the same forwards and backwards. A **substring** is a contiguous sequence of characters within a string.

Given a string `S`, count how many **distinct** substrings of `S` are palindromes.

Two substrings are considered the same if they have identical characters in identical positions; that is, we count each unique palindromic text once, regardless of how many times it appears as a substring.

## Input

A single line containing the string `S`, consisting of lowercase English letters.

```
S
```

## Output

Print a single integer: the number of distinct palindromic substrings of `S`.

## Examples

### Example 1
```
Input:
aba

Output:
4
```
The distinct palindromic substrings are `"a"`, `"b"`, `"aba"`, and `"a"` (but `"a"` is already counted), giving `4`. (The unique palindromic texts are `a`, `b`, `aba`.)

Wait — re-examining: palindromic substrings are `"a"`, `"b"`, `"a"`, `"aba"`. Distinct values are `a`, `b`, `aba`, so the answer is `3`.

```
Input:
aba

Output:
3
```

### Example 2
```
Input:
aaaa

Output:
4
```
Distinct palindromic texts: `"a"`, `"aa"`, `"aaa"`, `"aaaa"`.

### Example 3
```
Input:
abc

Output:
3
```
Each single character is a palindrome: `"a"`, `"b"`, `"c"`.

## Function Signature

```python
def solve(s: str) -> int:
    ...
```

## Notes

- `1 ≤ |S| ≤ 1000`.
- You only need to count distinct palindromic substrings by content, not by position.
- An efficient approach recognizes each palindrome by its center and expands outward, collecting unique results in a set.
