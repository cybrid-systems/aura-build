# Basic Calculator II

## Problem

Given a string `s` representing an arithmetic expression containing non-negative integers and the four basic operators `+`, `-`, `*`, `/` (with integer division truncated toward zero), evaluate the expression and return its result.

The expression is well-formed according to the following rules:

- Tokens are separated by **spaces** (i.e. the input may be read token-by-token, but you may also handle a space-less version if noted in the test data).
- No unary operators appear at the start of the expression.
- Integer division truncates toward zero (e.g. `6 / -2 == -3`, `-7 / 3 == -2`).
- All intermediate and final values fit within a signed 32-bit integer (`-2^31 ≤ result ≤ 2^31 - 1`).

## Function Signature

```
(solve s) -> int
```

- `s` — a string containing the expression.
- Returns the integer result of evaluating the expression.

## Input / Output Convention (Aura harness)

The harness feeds the problem **without stdin**. Each test case is provided by the runtime via a `CASE0=...` line in the surrounding environment. The function `solve` is invoked directly with the argument described below.

Example environment block:

```
CASE0_count=3
CASE0_0="3+2*2"
CASE0_1=" 3/2 "
CASE0_2=" 3+5 / 2 "
```

For each `i` from `0` to `count-1`, `solve` is called with the string `CASE0_i` and its return value is compared against the expected answer.

## Notes

- Multiplication and division have higher precedence than addition and subtraction. Evaluate `*` and `/` left-to-right before evaluating `+` and `-` left-to-right.
- Integer division must truncate toward zero (C/C++/Java-style truncation), **not** floor toward `-∞`.
- The expression length is at most `10^5`; an `O(n)` algorithm is expected.
