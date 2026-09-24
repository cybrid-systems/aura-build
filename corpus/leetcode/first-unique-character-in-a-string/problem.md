# First Unique Character in a String

## Problem Statement

Given a string `s`, find the **first non-repeating character** in it and return its **index**. If every character in the string repeats at least once, return `-1`.

A character is considered **non-repeating** if it appears **exactly once** in the string. The "first" such character is the one with the **lowest index**.

## Examples

```
Input:  s = "loveleetcode"
Output: 2
Explanation: 'l' appears at indices 0 and 1, 'o' appears at index 2 only — wait,
          'l', 'o', 'v', 'e', 'l', 'e', 'e', 't', 'c', 'o', 'd', 'e'
          'l' → appears twice, 'o' → appears twice, 'v' → once, 'e' → four times,
          't' → once, 'c' → once, 'd' → once.
          First unique is 'v' at index 2.
```

```
Input:  s = "aabbcc"
Output: -1
Explanation: Every character repeats, so no unique character exists.
```

```
Input:  s = "z"
Output: 0
Explanation: The single character is trivially unique.
```

## Function Signature

```clojure
(solve s)
```

- `s` — a string containing only lowercase English letters (`a-z`). Length is between 1 and 10^5.
- Returns — the 0-based index of the first unique character, or `-1` if none exists.

## Input / Output Convention (Aura harness)

The harness reads no stdin. Instead, each test case is provided to `solve` as its single argument, and results are written one per line in the following format:

```
CASE0=loveleetcode
CASE1=aabbcc
CASE2=z
```

Your `solve` function will be invoked once per `CASE` line. Produce one integer output per case, in order:

```
2
-1
0
```

## Notes

- **Efficiency matters**: the string length can be up to 10^5. Aim for a solution that runs in O(n) time with O(1) additional space (since the alphabet is fixed at 26 characters).
- A natural two-pass approach works well: first pass counts occurrences, second pass finds the first index with count equal to 1.
- Characters outside `'a'..'z'` are guaranteed not to appear, so a fixed-size 26-element array (or a `byte` array) suffices for counting.
