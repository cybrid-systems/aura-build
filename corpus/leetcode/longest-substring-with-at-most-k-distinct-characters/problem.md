# Longest Substring with At Most K Distinct Characters

## Problem

Given a string `s` consisting of lowercase English letters and an integer `k`, find the length of the longest contiguous substring of `s` that contains **at most `k` distinct characters**.

If `k` is `0`, or `s` is empty, the answer is `0`.

## Function Signature

```python
def solve(s: str, k: int) -> int:
    ...
```

## Input Format

The input is provided on standard input as a single line containing two space-separated values:

```
CASE0=<string>
CASE1=<k>
```

The harness decodes these lines into the function arguments:
- `CASE0` → the string `s`
- `CASE1` → the integer `k`

For example:

```
CASE0=eceba
CASE1=2
```

calls `solve("eceba", 2)`.

## Output Format

Your function must return a single integer: the length of the longest substring with at most `k` distinct characters.

For the example above, the expected return value is `3` (the substring `"ece"`).

## Notes

- The substring must be **contiguous**.
- "At most `k` distinct" means the count of unique characters in the substring must be `<= k`.
- A sliding-window approach with a frequency map runs in `O(n)` time, where `n = len(s)`.
