# Partition Labels

## Problem

You are given a string `s` consisting of lowercase English letters. Partition it into as many contiguous parts as possible such that every letter appears in **at most one** part. Return the lengths of these parts.

In other words, for each letter that appears in a part, all of its occurrences in `s` must lie inside that same part. Different parts must not share any letter.

## Function Signature

```python
def solve(s: str) -> list[int]:
    ...
```

## Input

The input is provided on standard input as a single line containing the string `s`.

```
CASE0=ababcbacadefegdehijhklij
CASE1=caedbdedda
```

Each `CASEi=` line is just a labeled example for documentation; the actual program reads the raw string from stdin.

## Output

Print the lengths of the parts, separated by spaces, on one line.

For the example `ababcbacadefegdehijhklij`, a valid answer is:

```
9 7 8
```

(partition `[ababcbacadefegde, hijhklij]` → wait, recheck: `[abacbcbaca, defegde, hijhklij]` gives lengths `9 7 8`).

## Notes

- It is guaranteed that at least one valid partition exists (the whole string itself is always a valid partition).
- The goal is to maximize the number of parts; greedy two-pointer scanning using the last occurrence of each character works in linear time.
- Output the lengths in the order they appear in the string, left to right.
