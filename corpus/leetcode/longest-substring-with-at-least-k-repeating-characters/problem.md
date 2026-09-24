# Longest Substring with At Least K Repeating Characters

## Problem

Given a string `s` consisting only of lowercase English letters and an integer `k`, find the length of the longest substring of `s` such that **every character that appears in the substring appears at least `k` times** within that substring.

If no such substring exists, return `0`.

## Function Signature

```python
def solve(s: str, k: int) -> int:
```

## Input Format (CASE0)

The harness supplies arguments directly to `solve`. A typical `CASE0` line for local testing looks like:

```
CASE0=s=aaabb; k=3; expect=3
```

- `s` — the input string (1 ≤ |s| ≤ 10^4, lowercase letters)
- `k` — the minimum required repetition (1 ≤ k ≤ |s|)
- `expect` — the expected return value

## Output Format

Return a single integer: the maximum length of a valid substring.

## Examples

| s          | k | Answer | Explanation                                      |
|------------|---|--------|--------------------------------------------------|
| `aaabb`    | 3 | 3      | `"aaa"` — every char (only `a`) appears ≥ 3 times |
| `ababbc`   | 2 | 5      | `"ababb"` — `a`×2, `b`×3                         |
| `aabbcc`   | 1 | 6      | whole string, since k=1 is trivially satisfied   |
| `abcdef`   | 2 | 0      | no character repeats twice                       |

## Notes

- A character appearing fewer than `k` times in the window disqualifies the window.
- An efficient approach bounds the number of *distinct* characters in the window (a sliding-window variant) and runs in roughly O(26·n) time.
- Edge cases: `k = 1` always returns `len(s)`; `k > len(s)` returns `0`.
