# Maximum Swap

## Problem

You are given a non-negative integer `n`. You may perform **at most one** operation: choose two distinct digit positions `i < j` in the decimal representation of `n` and swap the digits at those positions. After at most one swap, the resulting integer should be as large as possible.

Return that maximum integer.

## Function Signature

```haskell
solve :: String -> Int
```

The input is given as a string so that leading digits and the exact digit sequence are preserved without integer-overflow concerns; however, the answer is comfortably within standard `Int` range.

## Input

A single line containing the decimal representation of `n` (no leading zeros unless `n` is exactly `"0"`).

## Output

Print the maximum integer obtainable after performing at most one swap of two digits.

## Examples

```
CASE0=INPUT=2736
CASE0=OUTPUT=7236
CASE1=INPUT=9973
CASE1=OUTPUT=9973
CASE2=INPUT=98368
CASE2=OUTPUT=98863
CASE3=INPUT=0
CASE3=OUTPUT=0
```

## Notes

- If no swap improves the value, return the original number (the example `9973` is already the maximum reachable with one swap).
- Leading zeros are not an issue because swapping into the most-significant position is only beneficial when a strictly larger digit exists later in the string.
- Greedy strategy: for each position, swap in the largest digit that appears later (preferring the **rightmost** occurrence of that largest digit) if and only if it produces a strictly larger prefix.
