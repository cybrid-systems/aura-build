# Minimum Number of Flips to Make Binary String Alternating

## Problem

You are given a binary string `s` of length `n` consisting only of the characters `'0'` and `'1'`.

You may perform **at most one** rotation: take the last character of `s` and move it to the front (equivalently, any single character can be shifted from position `i` to position `i-1` for all `i >= 1`). After at most one such rotation, you want `s` to become an **alternating** binary string (no two adjacent characters are the same).

A **flip** changes a single character from `'0'` to `'1'` or from `'1'` to `'0'`. Find the minimum number of flips needed to achieve an alternating string, using **zero or one** rotation. If the string is already alternating, zero flips is acceptable; if no rotation can help make it alternating with flips, return the minimum flips achievable.

## Function Signature

```clojure
(defn solve [s] ...)
```

- `s` — a string containing only the characters `'0'` and `'1'`.
- Returns an integer: the minimum number of character flips required.

## Input / Output Convention

- The harness reads no stdin; instead each test case is provided inline.
- The first line is `CASE0=<value>` where `<value>` is the input string `s`.
- A second line `SOLVE0=<expected>` contains the expected integer answer (used by the grader, not by your function).
- Your `solve` function must return the minimum flips as an integer.

## Notes

- A single rotation is optional, not mandatory — you may also choose to keep `s` as is.
- An alternating string of length `n` must match one of exactly two patterns: `010101...` or `101010...`.
- A sliding-window approach over a length-`2n` virtual string (the original followed by itself) can be used to evaluate every possible rotation in O(n) time.
