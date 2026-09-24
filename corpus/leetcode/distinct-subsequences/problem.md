# Distinct Subsequences

## Problem Statement

Given two strings `s` (length `n`) and `t` (length `m`), count the number of **distinct** ways to obtain `t` as a subsequence of `s`. Return the count.

A subsequence is formed by deleting zero or more characters from `s` while keeping the relative order of the remaining characters. Two subsequences are considered the same if they use the same set of indices in `s`; identical strings reached through different index choices count as separate subsequences.

Formally, count the number of index sequences `0 ≤ i_1 < i_2 < ... < i_m < n` such that `s[i_k] == t[k]` for all `k = 1..m`.

Since the answer can be very large, return it modulo `10^9 + 7`.

## Function Signature

```python
def solve(s: str, t: str) -> int:
    """Return the number of distinct subsequences of s equal to t, mod 1_000_000_007."""
```

## Input / Output Convention

The harness invokes `solve(s, t)` directly with two string arguments. For example, a typical case looks like:

```
CASE0=("rabbbit", "rabbit")
CASE0_OUT=3
```

The expected return value is the count of distinct subsequences, modulo `10^9 + 7`.

## Notes

- An empty `t` is a subsequence of `s` in exactly **one** way (by deleting every character).
- If `m > n`, the answer is `0`.
- Use dynamic programming; a `O(n·m)` solution fits easily within standard limits, but a `O(n)` rolling solution is also straightforward.
- Remember to apply the modulo after every addition to avoid overflow.
