# Palindrome Partitioning

## Problem

Given a string `s`, partition `s` such that every substring of the partition is a palindrome. Return all possible palindrome partitionings of `s`.

A *palindrome* is a string that reads the same backward as forward (e.g., `"aba"`, `"a"`, `"racecar"`).

Your task is to enumerate **every** way to split `s` into contiguous pieces so that each piece is a palindrome. The order of partitions in the output does not matter.

## Function Signature

```clojure
(defn solve [s]
  ;; returns a sequence of partitions
  ;; each partition is a sequence of palindromic strings whose concatenation is s
  )
```

## Input

The harness invokes `(solve s)` where `s` is a non-empty string. No stdin is read.

## Output (I/O Convention)

The harness formats the result as `CASE0=` lines. A return value of

```clojure
[["a" "a" "b"]
 ["aa" "b"]]
```

is rendered as:

```
CASE0=[["a","a","b"],["aa","b"]]
```

Each inner sequence is a partition: its elements are palindromic substrings concatenated in order that reconstruct `s`.

## Examples

- `s = "aab"` → partitions: `[["a","a","b"], ["aa","b"]]`
- `s = "a"` → partitions: `[["a"]]`
- `s = "aba"` → partitions: `[["a","b","a"], ["aba"]]`
- `s = "abba"` → partitions: `[["a","b","b","a"], ["a","bb","a"], ["abba"]]`

## Notes

- The string consists of letters only; treat it case-sensitively.
- The order of the returned partitions is not significant, but each must be distinct as a sequence.
- The partition `["a","a","b"]` is considered different from `["aa","b"]` — both must appear for `"aab"`.
