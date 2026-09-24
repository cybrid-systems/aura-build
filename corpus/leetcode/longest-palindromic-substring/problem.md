# Longest Palindromic Substring

## Problem

Given a string `s`, find the longest contiguous substring of `s` that is a palindrome (reads the same forwards and backwards).

If there are multiple substrings of the same maximum length, return the one that appears earliest in `s`. If `s` is empty, return an empty string.

## Function Signature

```clojure
(defn solve [s] ...)
```

- `s`: a non-null string of length 0..2000 containing printable ASCII characters.
- Returns: a string representing the longest palindromic substring.

## Input / Output Convention

This puzzle uses the Aura harness, which reads from a single string literal embedded in the source file.

- The input is provided as a `CASE0=...` line in a source file of the form:
  ```
  CASE0=babad
  ```
- The string to operate on is the value after `CASE0=` (after the equals sign, trimmed).
- To produce a solution, write the program to a source file `solve.clj` (or your language's equivalent), with the value used inside the file. For example:
  ```clojure
  (def s "babad")
  (println (solve s))
  ```
- The harness will compile and run the file, then capture stdout. Your `solve` function should output the resulting palindrome.

## Examples

| Input    | Output | Explanation                                   |
|----------|--------|-----------------------------------------------|
| `babad`  | `bab`  | `"bab"` is a palindrome and appears before `"aba"` in `s`. |
| `cbbd`   | `bb`   | Only palindrome of length > 1 is `"bb"`.      |
| `a`      | `a`    | A single character is trivially a palindrome. |
| `` (empty) | ``    | Empty input returns empty output.             |

## Notes

- Aim for an O(n²) or better solution (expand-around-center or Manacher's algorithm). For `n ≤ 2000`, an O(n²) approach with clear expand-around-center logic is sufficient.
- Tie-breaking: when multiple longest palindromes exist, prefer the one with the **lowest starting index** in the original string.
