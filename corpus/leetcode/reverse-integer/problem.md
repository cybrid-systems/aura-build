# Reverse Integer

## Problem

Given a signed 32-bit integer `x`, return the digits of `x` reversed, keeping the sign. If the reversed integer overflows the signed 32-bit range `[−2^31, 2^31 − 1]`, return `0` instead.

## Function Signature

```python
def solve(x: int) -> int:
    ...
```

## Input

A single line containing the integer `x`.

```
CASE0=-123
CASE1=1534236469
CASE2=-2147483412
CASE3=0
CASE4=120
```

- `CASE0` → expected output `-321`
- `CASE1` → expected output `0` (reverses to `9646324351`, overflow)
- `CASE2` → expected output `-2143847412`
- `CASE3` → expected output `0`
- `CASE4` → expected output `21` (trailing zeros dropped)

## Output

Print the reversed integer, or `0` on overflow.

## Notes

- Handle the sign separately so that `-123` becomes `-321`.
- Detect overflow during digit extraction rather than after the fact, to avoid working with out-of-range Python values silently.
- The valid range is `INT_MIN = -2**31` and `INT_MAX = 2**31 - 1`.
