# Substring with Concatenation of All Words

## Problem

You are given a string `s` and an array of strings `words` (all words have the same length). Find all starting indices of substrings in `s` that are a **concatenation of each word in `words` exactly once**, in any order, without any extra characters between or around them.

- Words are distinct (no duplicates in `words`).
- Return a list of all such starting indices, in ascending order.
- If no such substring exists, return an empty list.

## Function Signature

```python
def solve(s: str, words: List[str]) -> List[int]:
    ...
```

## Input / Output Convention

The harness reads two lines from the case file:

```
CASE0=<value of s>
CASE1=<value of words as a JSON array of strings>
```

Your `solve` function receives `s` and `words` parsed from these lines and must return a list of integer indices.

### Example

```
CASE0=barfoothefoobarman
CASE1=["foo","bar"]
```

Expected output:

```
[0, 9]
```

Explanation: `"barfoo"` starts at index `0` and `"foobar"` starts at index `9`. Each is a concatenation of `"foo"` and `"bar"` (each word used exactly once).

## Notes

- Let `n = len(s)`, `m = len(words)`, `w = len(words[0])`. The concatenated substring length is always `m * w`.
- Only the first `w` offsets modulo `w` need to be considered as starting points for the sliding window — this keeps the solution efficient.
- The output order must be ascending.
