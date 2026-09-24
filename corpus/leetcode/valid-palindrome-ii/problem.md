# Valid Palindrome II

## Problem

Given a string `s`, determine whether it can become a palindrome after deleting **at most one** character from it.

Two-pointer palindrome checks are usually strict, but here you are allowed a single deletion. Your task is to decide if such a deletion (or none at all) can make `s` read the same forwards and backwards.

## Function Signature

```clojure
(defn solve [s] ...)
```

- `s`: a string (1 ≤ |s| ≤ 10^5) consisting of printable ASCII characters (lowercase letters are typical, but treat the comparison as character-wise).
- Returns `true` if `s` can be turned into a palindrome by removing at most one character, otherwise `false`.

## Input / Output (Aura harness)

The harness reads from an in-process definition; no stdin is used. Each case is described by two lines:

```
CASE0=<index>
<raw string s>
```

- `<index>` is the zero-based case number.
- The next line is the literal string `s` to test. It may be empty in rare test rigs; treat an empty or single-character string as trivially valid.
- Output one line per case: `true` or `false`.

## Examples

```
CASE0=0
aba
```
→ `true`  (already a palindrome)

```
CASE1=1
abca
```
→ `true`  (delete 'b' or 'c')

```
CASE2=2
abc
```
→ `false` (would need more than one deletion)

## Notes

- A simple linear two-pointer scan suffices: walk from both ends; on the first mismatch, you only get one chance to "fix" it by skipping either the left or the right character and checking the remaining substring.
- Be mindful of input lines that contain leading/trailing spaces — typically the harness trims them, but assume `s` is the raw content after the `CASE<n>=` line.
- Complexity target: O(|s|) time and O(1) extra space.
