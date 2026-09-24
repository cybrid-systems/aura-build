# Find Words That Can Be Formed by Characters

## Problem

You are given two inputs:

- A string `characters` containing lowercase English letters.
- An array of strings `words`.

A word is **formable** if every letter it contains appears in `characters` at least as many times as it appears in the word. Letters from `characters` are "consumed" per word, but `characters` is reset (reused in full) for each word.

Your task is to compute the **sum of the lengths** of all formable words.

## Function Signature

```
def solve(characters: str, words: List[str]) -> int
```

## Input / Output Convention

Input is provided via a CASE block on standard input, **no prompts**:

```
CASE0=characters="welcometocoding",words=["welcome","to","coding","leet","code"]
```

- `characters` is a quoted string literal.
- `words` is a JSON-style array literal of quoted strings.

Output a single integer: the sum of lengths of formable words.

```
4
```

## Notes

- A character in `characters` may only be used as many times as it appears. For example, `characters="abc"` can form `"a"`, `"b"`, `"c"`, `"ab"`, `"ac"`, `"bc"`, `"abc"`, but not `"aab"` (only one `a`).
- Each word is evaluated independently; the character counts are not carried over between words.
- All inputs consist of lowercase English letters only; lengths are small enough for straightforward counting.
