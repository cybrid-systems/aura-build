# Multiply Strings

## Problem

You are given two non-negative integers, each provided as a decimal string (with no leading zeros except for the number `"0"` itself). Compute their exact product and return it as a decimal string.

You must **not** rely on built-in big-integer arithmetic libraries or on direct conversion of the entire input into a native integer type. Solve the problem by manipulating digits and arrays.

## Function Signature

```python
def solve(a: str, b: str) -> str:
    ...
```

The harness will pass the two operand strings as arguments and expect the product as a return value.

## Input / Output Convention (CASE0)

Because this harness does not use stdin, each test case is supplied as a line on standard input of the form:

```
CASE0=<a>|<b>
```

For example:

```
CASE0=123|456
```

Your `solve` function receives `a = "123"` and `b = "456"` and must return `"56088"`.

- `a` and `b` are decimal strings consisting only of characters `'0'–'9'`.
- Each string has length between `0` and `200` characters (an empty string denotes the value `0`).
- There are no leading zeros unless the string is exactly `"0"`.

## Examples

| a      | b        | Expected output |
|--------|----------|-----------------|
| `2`    | `3`      | `6`             |
| `123`  | `456`    | `56088`         |
| `0`    | `99`     | `0`             |
| `999`  | `999`    | `998001`        |

## Notes

- Handle the edge cases where either operand is empty or `"0"` by returning `"0"`.
- An `O(n·m)` digit-array algorithm (long multiplication on reversed digit arrays) is sufficient and expected; the maximum result length is `len(a) + len(b)` digits.
