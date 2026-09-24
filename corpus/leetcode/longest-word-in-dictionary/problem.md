# Longest Word in Dictionary

## Problem

Given an array of strings `words` representing a dictionary, find the longest word that can be built one character at a time by other words in the dictionary.

A word `w` can be built one character at a time if, for every prefix `p` of `w`, the string `p` is also present in `words`. For example, `"abc"` is buildable if `"a"` and `"ab"` are both in `words`.

Return the longest such word. If there is more than one candidate of the same maximum length, return the one that is **lexicographically smallest**. If no word qualifies, return `""`.

## Function Signature

```haskell
solve :: [String] -> String
```

- **Input**: A list of dictionary words (each word is a non-empty string of lowercase English letters).
- **Output**: A single string — the answer described above.

## I/O Convention (Aura harness)

The harness drives the solution via standard input. The format is:

```
CASE0=<n>
CASE0.WORDS[0]=<word0>
CASE0.WORDS[1]=<word1>
...
CASE0.WORDS[n-1]=<word_{n-1}>
ANSWER=<expected_string>
```

Lines beginning with `CASE0=` describe a single test case: `n` is the number of words, followed by `n` lines of `CASE0.WORDS[i]=<word>`. The `ANSWER=` line gives the expected output for verification. Words may repeat; duplicates should be treated as a single entry.

The `solve` function receives the parsed list of words (in the order given) and must return the answer as a `String`.

## Notes

- Sorting the words and inserting them into a trie is a natural approach: a word qualifies exactly when every prefix node along its path is marked as a complete word.
- The lexicographically-smallest tie-breaker matters only when two valid words share the same maximum length; standard lexicographic comparison (`a < b`) is sufficient because the alphabet is lowercase English.
- Complexity target: `O(sum of word lengths)` time and `O(sum of word lengths)` additional space.
- Example: `words = ["w","wo","wor","worl","world"]` → answer `"world"`.
- Example: `words = ["a","banana","app","appl","ap","apply","apple"]` → answer `"apple"` (`"apply"` has the same length but `"apple"` < `"apply"`).
