# Reorganize String

## Statement

Given a string `s` consisting of lowercase English letters, rearrange its characters so that **no two adjacent characters are the same**. Return any such valid rearrangement, or an empty string if it is impossible.

Formally, given the multiset of characters from `s`, produce a permutation `t` of those characters such that for every index `i` with `0 ≤ i < |t| − 1`, `t[i] ≠ t[i+1]`. If no such permutation exists, return `""`.

A rearrangement is impossible when the count of some character exceeds `⌈n / 2⌉`, where `n = |s|` (this includes the trivial case `n = 1`, which is always valid).

## Function Signature

```lisp
(defun solve (s)
  ;; s is a string of lowercase letters
  ;; returns a rearranged string, or "" if impossible
  )
```

## Input / Output Convention

Input is supplied via a single `CASE0=...` line on standard input (no separate stdin framing needed by the caller).

```
CASE0=aaab
```

The function `solve` is invoked on the value associated with `CASE0` (the raw string `aaab`). It should return a string.

For the example above, a valid return value is `"aaba"`. Another is `"abaa"`. The return value `""` would be incorrect here because a valid rearrangement exists.

For `s = "aaab"`, no valid rearrangement exists; `solve` must return `""`.

## Notes

- `n` is at most `10^5`; an `O(n log n)` or `O(n)` algorithm is expected.
- A standard approach is greedy: repeatedly place the most frequent remaining character that differs from the last placed one (e.g., using a max-heap keyed by remaining count). An equivalent approach is to interleave the two most frequent groups.
- Tie-breaking among equal-count characters does not matter as long as adjacency is respected.
- The empty input string (`""`) is trivially valid; return `""`.
