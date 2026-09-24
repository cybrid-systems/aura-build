# Permutation in String

## Problem

You are given two strings `s1` and `s2`. Determine whether `s2` contains any substring that is a permutation of `s1`.

In other words, return `True` if there exists an index `i` such that `s2[i : i + len(s1)]` is a permutation of `s1`, and `False` otherwise.

Both strings consist of lowercase English letters. Assume `1 ≤ len(s1) ≤ len(s2) ≤ 10^5`.

## Function Signature

```python
def solve(s1: str, s2: str) -> bool:
    ...
```

## Input / Output Convention

This task uses a **CASE** style harness. Each test case is provided on a single line with two space-separated strings:

```
CASE0=abc abcbacab
CASE1=abc cab
CASE2=abcd dabc
CASE3=hello oooll
```

- The substring before the first `=` is the case identifier.
- After the `=`, two space-separated strings are provided: `s1` and `s2`.

For each case, output one line in the form:

```
CASE0=True
CASE1=True
CASE2=True
CASE3=False
```

## Notes

- An efficient solution slides a fixed-size window of length `len(s1)` across `s2` and compares character frequency counts (e.g., using a counter array of size 26). A naive `O(n · m)` check of all substrings will be too slow for `len(s2) = 10^5`.
- Edge case: when `s1` and `s2` have the same length, the answer is simply whether the two strings are anagrams of each other.
