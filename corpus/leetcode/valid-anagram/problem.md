# Valid Anagram

Given two strings `s` and `t`, determine if they are anagrams of each other. Two strings are anagrams if they contain the same characters with the same frequencies (regardless of order). For this problem, assume the strings consist only of lowercase English letters (`'a'` to `'z'`).

Write a function `solve(s, t)` that returns `True` if the strings are anagrams of each other, and `False` otherwise.

## Function Signature

```python
def solve(s: str, t: str) -> bool:
```

## Input

The input is read from standard input in the following format:

```
CASE0=<string s>
CASE1=<string t>
```

Each line contains the literal string value (no quotes, no escaping). The two strings are non-empty and consist only of lowercase English letters.

## Output

Print a single line containing either `True` or `False`, indicating whether `s` and `t` are anagrams.

## Examples

### Example 1
Input:
```
CASE0=listen
CASE1=silent
```
Output:
```
True
```

### Example 2
Input:
```
CASE0=hello
CASE1=world
```
Output:
```
False
```

## Notes

- An anagram uses exactly the same characters the same number of times, just rearranged.
- Strings of different lengths can never be anagrams of each other.
- The expected time complexity is **O(n)** where `n` is the length of the strings, using a frequency count of characters.
- The expected space complexity is **O(1)** (a fixed-size array of 26 letters suffices for lowercase English letters).
