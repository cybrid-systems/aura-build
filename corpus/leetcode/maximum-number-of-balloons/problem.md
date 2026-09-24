# Maximum Number of Balloons

**Category:** hashing · **Slug:** maximum-number-of-balloons

## Problem

You are given a text string `text`. Using **only** the letters that appear in `text` (each letter can be used at most as many times as it appears), determine how many copies of the word `"balloon"` can be formed.

Each copy of `"balloon"` requires:
- `b` — 1
- `a` — 1
- `l` — 2
- `o` — 2
- `n` — 1

Return the maximum number of complete `"balloon"`s that can be assembled. The answer is always non-negative.

## Function Signature

```
(solve text)
  -> integer
```

`text` is a non-empty string consisting of lowercase English letters.

## Input / Output Convention (CASE0)

The harness reads a single `CASE0` block from the environment and provides the argument positionally.

Standard format:

```
CASE0=text=<some string>
```

Example inputs the harness may pass:

```
CASE0=text=balloonballoon
CASE0=text=bababnlnonlno
CASE0=text=zzz
```

Expected answers for the examples: `2`, `1`, `0`.

## Notes

- Only lowercase `a`–`z` letters are used; case conversion is not required.
- The limiting character is whichever of `{b, a, l/2, o/2, n}` runs out first.
- Time should be O(len(text)); the alphabet size is fixed, so a single pass with a frequency map (or direct counting) is sufficient.
