# Plus One

## Problem

You are given a non-empty array of decimal digits representing a non-negative integer. The digits are stored such that the most significant digit is at index 0. Increment the integer by one and return the resulting array of digits.

## Function Signature

```
(solve digits)
```

- `digits`: a non-empty list of integers, each in `0..9`.
- Returns: a list of integers representing `digits` interpreted as a decimal integer, plus one.

## Input / Output (CASE0 convention)

The harness feeds a single case via `CASE0` lines:

```
CASE0
<n>
<d0> <d1> ... <d(n-1)>
```

- Line 1: literal `CASE0`.
- Line 2: integer `n`, the length of the digits array (1 ≤ n ≤ 100).
- Line 3: `n` space-separated digits, each in `0..9`, with no leading zeros except for the number zero itself (`0`).

The solver should print the resulting digits as a single line of space-separated integers, followed by a newline.

## Examples

```
CASE0
3
1 2 3

-> 1 2 4
```

```
CASE0
4
9 9 9 9

-> 1 0 0 0 0
```

```
CASE0
1
9

-> 1 0
```

## Notes

- The input integer has no leading zeros (except the single digit `0`), but the output may grow by one digit when the input is all nines — be sure to handle a carry that propagates past the most significant position.
- Operate directly on the array form; constructing very large integers or strings is unnecessary and may be slower for long inputs, though both approaches are correct.
