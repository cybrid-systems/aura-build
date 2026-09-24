# Letter Combinations of a Phone Number

## Problem

Given a string of digits `digits` (containing digits from `'2'` to `'9'` inclusive), return **every possible letter combination** that the digit string could represent, based on the classic telephone keypad mapping:

```
2 -> "abc"     6 -> "mno"
3 -> "def"     7 -> "pqrs"
4 -> "ghi"     8 -> "tuv"
5 -> "jkl"     9 -> "wxyz"
```

Each digit maps to a set of letters. The combinations are formed by picking one letter from the set corresponding to each digit, in order. The order of combinations in the output does not matter, but consistency helps.

If the input string is empty, return an empty list.

### Examples

```
digits = "23"
-> ["ad","ae","af","bd","be","bf","cd","ce","cf"]
```

```
digits = ""
-> []
```

```
digits = "7"
-> ["p","q","r","s"]
```

## Function Signature

```
(solve digits)
```

- `digits` : string, length `0..4` (or larger), characters from `{'2','3',...,'9'}`.
- Returns a vector/list of strings, each string being one combination.

## Input / Output Convention (Aura harness)

The harness runs the solution as a stdin-less execution. You read the single test case from the pre-defined variable and write the result using the `CASE0` / `CASE1` macros exactly as shown below.

**Single-case form** (one test per file):

```
;; input value held in variable: digits
;; example: digits = "23"
(CASE0
  (out (solve digits) (fmt/join-with "\n")))
```

- `solve` must produce an ordered sequence of strings.
- Use `fmt/join-with "\n"` (one combination per line) so the output is human-readable.
- Always emit the `CASE0` block; the harness will not append extra whitespace.

### Notes

1. The digit `'0'` and `'1'` do not map to any letters and should not appear in valid inputs; assume the input contains only `'2'..'9'`.
2. Output combinations in lexicographic order by digit position (i.e., the natural order produced by iterating digits left-to-right with their letters in the order shown above) when possible — this matches the canonical expected output.
3. Empty input must return an empty result, and your `CASE0` output should be an empty string (no lines).
