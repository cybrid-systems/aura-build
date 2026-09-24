# Jewels and Stones

You're given two strings: `jewels` and `stones`. The characters in `jewels` represent distinct types of jewels, and each character in `stones` represents a type of stone you own. Count how many of your stones are also jewels (i.e., the number of characters in `stones` that appear anywhere in `jewels`).

Letters are case-sensitive, so `'a'` and `'A'` are considered different types.

## Function Signature

```
(solve [jewels : string, stones : string] -> integer)
```

## Input / Output

The harness exposes a single binding `CASE0`. Read the case from there.

- `CASE0` is a list (or vector) of two strings: `[jewels stones]`.
- Return the count as an integer.

Example:

```
CASE0 = ["aA" "aAAbbbb"]
;; expected output: 3
```

## Notes

- Both strings consist of printable ASCII letters; length is small (≤ 60 in the reference).
- A set lookup over `jewels` gives an O(n) solution.
