# Integer to Roman

## Problem Statement

Convert a given integer into its Roman numeral representation using the standard subtractive notation rules.

Roman numerals use seven symbols:

| Value | Symbol |
|-------|--------|
| 1     | I      |
| 5     | V      |
| 10    | X      |
| 50    | L      |
| 100   | C      |
| 500   | D      |
| 1000  | M      |

Roman numerals are typically written from largest to smallest, left to right. However, in a small set of specific cases, a smaller numeral placed before a larger one indicates subtraction. These subtractive forms are:

- **I** before **V** (5) and **X** (10) → 4 and 9
- **X** before **L** (50) and **C** (100) → 40 and 90
- **C** before **D** (500) and **M** (1000) → 400 and 900

For example:
- 58 → `LVIII` (L + V + III)
- 1994 → `MCMXCIV` (M + CM + XC + IV)
- 9 → `IX`
- 3999 → `MMMCMXCIX`

Your task is to produce the Roman numeral string for any valid input.

## Function Signature

```
solve(n: int) -> str
```

## Input / Output Convention

The harness drives `solve` directly. No stdin is read and no stdout is written by your code.

Test cases are provided as `CASE0` / `CASE1` / … lines below, each specifying the integer input and the expected Roman numeral output:

```
CASE0=58:LVIII
CASE1=1994:MCMXCIV
CASE2=9:IX
CASE3=3999:MMMCMXCIX
CASE4=4:IV
CASE5=40:XL
CASE6=90:XC
CASE7=400:CD
CASE8=900:CM
CASE9=1:I
CASE10=3888:MMMDCCCLXXXVIII
```

## Notes

- The integer is guaranteed to be in the range **1 … 3999**, so the output will contain at most a few thousand characters' worth of standard symbols (`M`s at the front).
- Avoid emitting more than three consecutive identical symbols in a row; instead use the appropriate subtractive form (`IV`, `IX`, `XL`, `XC`, `CD`, `CM`).
- A greedy approach that consumes the input from the largest value to the smallest produces a correct result in linear time.
