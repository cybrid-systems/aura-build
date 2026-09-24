# Reverse Vowels of a String

## Problem

Given a string `s`, reverse **only** the vowel characters that appear in it, while leaving all other characters (consonants, digits, punctuation, spaces) in their original positions. The set of vowels to consider is the five lowercase letters `a, e, i, o, u`.

For example, the string `"hello"` becomes `"holle"`, and `"leetcode"` becomes `"leotcede"`.

If a character appears multiple times, every occurrence of a vowel participates in the reversal as a group: the first vowel in the string swaps with the last vowel, the second vowel swaps with the second-to-last vowel, and so on.

## Function Signature

```clojure
(defn solve [s] ...)
```

- **Input:** a single string `s` (1 ≤ |s| ≤ 10^5), consisting of printable ASCII characters.
- **Output:** a new string of the same length where the vowels of `s` appear in reversed order, with all non-vowel characters unchanged.

## I/O Convention (Aura harness, stdin-less)

Each test case is provided on its own block of named constants. Example:

```
CASE0.S="hello"
CASE0.ANSWER="holle"
CASE1.S="leetcode"
CASE1.ANSWER="leotcede"
CASE2.S="aA"
CASE2.ANSWER="aA"
```

The harness will call `(solve CASE0.S)` and compare the returned value against `CASE0.ANSWER`.

## Notes

- Only lowercase vowels (`a, e, i, o, u`) are considered vowels for this problem; treat uppercase letters and any other non-lowercase-vowel characters as non-vowels and leave them in place.
- An efficient solution uses a two-pointer scan from both ends of the string in a single pass.
