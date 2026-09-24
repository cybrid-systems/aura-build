# Most Common Word

## Problem Statement

Given a paragraph (a string containing letters, spaces, and punctuation) and a list of banned words, find the word that occurs most frequently in the paragraph **and** is not in the banned list. Words are case-insensitive, so `Hello`, `hello`, and `HELLO` are treated as the same word. Punctuation characters do not count as part of a word. Return the most common qualifying word in lowercase. If no non-banned word exists, return an empty string.

Assume the paragraph is non-null and may contain Unicode letters; assume the banned list contains lowercase tokens.

## Function Signature

```clojure
(defn solve [paragraph banned] ...)
```

- `paragraph` — a `String` containing the raw paragraph text.
- `banned` — a vector of `String` banned words (already lowercase).
- Returns a `String` — the lowercase most-common non-banned word, or `""` if none qualify.

## Input Convention (stdin-less harness)

The harness invokes `(solve paragraph banned)` directly. There is no `CASE0=` block because the function takes its inputs as arguments rather than reading stdin. Example harness wiring:

```
CASE0=("Bob hit a ball, the hit BALL flew far after it was hit." ["hit"])
CASE0_EXPECTED="ball"
```

## Notes

- Normalize case before counting; return the answer in lowercase.
- Strip punctuation from tokens; splitting on whitespace and removing non-letter characters is sufficient.
- Ties: if multiple words share the highest count, return any one of them (the judge accepts the set of valid answers).

## Example

```
solve "Bob hit a ball, the hit BALL flew far after it was hit." ["hit"]
;; => "ball"
```

Counts after normalization and banning `hit`: `ball` → 2, `bob` → 1, `a` → 1, `the` → 1, `flew` → 1, `far` → 1, `after` → 1, `it` → 1, `was` → 1. The winner is `ball`.
