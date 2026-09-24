# Fraction to Recurring Decimal

Given two integers `numerator` and `denominator`, compute their fraction as a string in decimal form. If the decimal part repeats, enclose the repeating portion in parentheses.

If the result is an integer, return it with no decimal point or parentheses. A negative result must be prefixed with `-`.

If numerator is 0, return `"0"`.

Note: Assume `denominator != 0`. Both integers fit in 32-bit signed range, but intermediate values (e.g., the quotient and remainder during long division) may exceed 32-bit; use 64-bit arithmetic.

## Function Signature

```python
def solve(numerator: int, denominator: int) -> str:
    ...
```

## Input / Output Convention

Input is supplied via a local harness as `CASE0=...` style lines, for example:

```
CASE0=numerator=1; denominator=2
CASE1=numerator=2; denominator=1
CASE2=numerator=4; denominator=333
```

Each `CASEn` line describes one test case. Multiple `CASE` lines may appear; your `solve` is invoked once per case (the harness feeds arguments directly to `solve`, not via stdin). The return value of `solve` is checked against the expected string.

Output for the samples above:

```
CASE0=0.5
CASE1=2
CASE2=0.(012)
```

## Notes

- Use long division: repeatedly multiply the remainder by 10, record the quotient digit, and track each remainder's position in the fractional part via a dictionary.
- When a remainder repeats, the digits generated since its first occurrence form the repeating cycle; insert parentheses around them and stop.
- Pay attention to sign: the result is negative when exactly one of the two inputs is negative.
- Watch the `-2^31 / -1` edge case, which overflows 32-bit but is representable in 64-bit as `2^31`.
