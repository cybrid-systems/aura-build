# Find All Anagrams in a String (Variant)

## Problem

You are given two strings `s` and `p`. An **anagram** of `p` is any permutation of its characters. Return the list of all starting indices in `s` where a contiguous substring of length `|p|` is an anagram of `p`. The indices should be returned in increasing order.

## Function Signature

```python
def solve(s: str, p: str) -> list[int]
```

## Input / Output Convention

Your function receives two arguments:

- `s`: the haystack string (lowercase letters, length 1..200000)
- `p`: the pattern string (lowercase letters, length 1..|s|)

It must return a list of integers: every index `i` such that `s[i : i + len(p)]` is an anagram of `p`, sorted in ascending order.

### Sample I/O

```
CASE0 s="cbaebabacd" p="abc"          -> [0, 6]
CASE1 s="abab"      p="ab"           -> [0, 1, 2]
CASE2 s="aaaaa"     p="aa"           -> [0, 1, 2, 3]
CASE3 s="abcd"      p="efgh"         -> []
CASE4 s="abdc"      p="abcd"         -> []
```

## Notes

- Use a sliding window of length `|p|` and frequency counts to achieve O(|s| + |p|) time.
- When `|p| > |s|`, the result is always an empty list.
- The output list is empty (not `null`) when no anagram is found.
