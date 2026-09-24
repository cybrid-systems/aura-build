# Add Binary

## Problem

You are given two binary strings `a` and `b` (each containing only the characters `'0'` and `'1'`). Compute the sum of the two numbers they represent and return it as a binary string.

The inputs are not guaranteed to have the same length, and either string may be empty or consist of a single character. The result must not contain leading zeros unless the value itself is zero.

## Function Signature

```python
def solve(a: str, b: str) -> str:
```

## Input Convention

The harness feeds the two strings via environment variables rather than stdin. Your `solve` function must accept them as parameters.

For verification, the driver evaluates:

```
CASE0_INPUT_a=11
CASE0_INPUT_b=1
CASE0_EXPECTED=100
CASE1_INPUT_a=1010
CASE1_INPUT_b=1011
CASE1_EXPECTED=10101
```

Each `CASE*n_INPUT_*` line provides a single argument; `CASE*n_EXPECTED` provides the expected return value.

## Notes

- Treat the strings as binary representations of non-negative integers.
- A linear scan from the least significant bit is sufficient; no big-integer libraries are needed.
- Handle carries correctly when both bits are `'1'`, or when a carry propagates past the most significant position.
