# Longest Repeating Character Substitution

## Problem

You are given a string `s` consisting of uppercase English letters, and an integer `k`. In one operation you may choose any character in `s` and change it to any other uppercase letter. Find the length of the longest substring that can be turned into a string of all identical characters using **at most** `k` operations.

In other words, for every window of `s`, you need at most `k` changes to make every character in the window equal — maximize the window length.

## Input

- A single line containing the string `s` (only uppercase English letters, `1 ≤ |s| ≤ 10^5`).
- A single line containing the integer `k` (`0 ≤ k ≤ |s|`).

## Output

A single integer: the length of the longest substring obtainable with at most `k` replacements.

## Function Signature

```clojure
(solve s k)
```

- `s` — string, the input string.
- `k` — long, the maximum number of allowed character replacements.
- Returns a `long` — the length of the longest valid substring.

## Notes

- A window of length `w` needs exactly `w - (max frequency of any letter inside the window)` replacements to become uniform.
- A window is valid iff that required count is `≤ k`. Use a sliding window with a frequency count over the current window.
- Time complexity `O(|s|)` is expected; the alphabet size is fixed at 26.

## Example

```
CASE0=ABAB
CASE0_K=2
ANSWER0=4
```

Explanation: pick the whole string — replace the two `B`s with `A`s (or vice versa) using `k = 2` replacements, giving a uniform string of length 4.

```
CASE1=AABABBA
CASE1_K=1
ANSWER1=4
```

Explanation: the longest window requiring at most 1 replacement has length 4 (e.g., indices 0–3 → `AABA`).
