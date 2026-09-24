# Longest Common Subsequence

Given two strings, find the length of the longest subsequence that is common to both. A *subsequence* is a sequence that can be derived from the given string by deleting zero or more characters without changing the relative order of the remaining characters.

## Function Signature

```clojure
(defn solve [s t] ...)
```

- `s` — the first input string.
- `t` — the second input string.
- Returns the length of the longest common subsequence of `s` and `t`.

## Input

The input is provided via the harness using the `CASE0=...` convention. Two cases are read from the environment:

```
CASE0=ABCBDAB
CASE1=BDBACA
```

- `CASE0` holds the first string (`s`).
- `CASE1` holds the second string (`t`).

Your `solve` function is called once with `s` and `t`, and your answer must be printed to standard output.

## Output

A single integer: the length of the longest common subsequence of `s` and `t`.

For the example above, one longest common subsequence is `BCAB` (length 4), so the expected output is:

```
4
```

## Notes

- Both strings are non-empty and consist of uppercase English letters.
- The expected time complexity is `O(len(s) * len(t))`, achievable via standard dynamic programming over prefixes.
- If you only need the *length*, you can keep a rolling 1D DP array of size `len(t) + 1`.
