# Isomorphic Strings

## Problem

Two strings `s` and `t` are **isomorphic** if the characters in `s` can be replaced (using a one-to-one mapping) to get `t`. That is, every character in `s` maps to exactly one character in `t`, and no two different characters in `s` map to the same character in `t`.

Given two strings `s` and `t`, determine if they are isomorphic.

## Function Signature

```python
def solve(s: str, t: str) -> bool:
    ...
```

## Input / Output

The harness feeds each test case on stdin in the following line-based form:

```
CASE0=s,egg
CASE1=foo,bar
CASE2=paper,title
CASE3=ab,aa
```

For each `CASEi=<a>,<b>` line, the solver is invoked with `s = <a>` and `t = <b>` (the comma is the separator; the strings themselves contain no commas). The expected return is a boolean, which the harness compares to the reference answer.

## Notes

- The mapping must be **bijective**: if `s[i] == s[j]` then `t[i] == t[j]`, and if `t[i] == t[j]` then `s[i] == s[j]`. Both directions must be checked.
- A single pass with two hash maps (one in each direction) is sufficient; an alternative is to canonicalize both strings by first-seen indices and compare.
- Edge case: strings of length 0 are isomorphic (trivially).
- Characters are general Unicode, not limited to ASCII.
