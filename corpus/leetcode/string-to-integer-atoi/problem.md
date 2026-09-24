# String to Integer (atoi)

## Problem

Implement the `myAtoi(string s)` function, which converts a string to a 32-bit signed integer following a specific set of rules. The function should perform the following steps in order:

1. **Whitespace:** Discard any leading whitespace characters.
2. **Signedness:** Determine the sign by checking if the next character is `'-'` or `'+'`. Assume positivity if neither is present.
3. **Conversion:** Read the integer characters by reading digits until the next non-digit character or the end of the string is reached. No other characters are valid after the sign.
4. **Rounding:** Round the result to the 32-bit signed integer range `[-2^31, 2^31 - 1]`. Specifically, values less than `-2^31` should be clamped to `-2^31`, and values greater than `2^31 - 1` should be clamped to `2^31 - 1`.

Return the resulting integer.

## Function Signature

```python
def solve(s: str) -> int:
    ...
```

## Input Format

The input is provided on a single line containing the string `s`. Note that the string may contain arbitrary characters (including spaces, letters, symbols) and its length is in the range `[0, 10^4]`.

```
CASE0="42"
CASE1="   -042"
CASE2="1337c0d3"
CASE3="0-1"
CASE4="words and 987"
CASE5="-91283472332"
CASE6="+1"
CASE7="   +0 123"
CASE8="2147483648"
CASE9="-2147483649"
CASE10=""
```

## Output Format

For each test case, print a single line containing the integer produced by `myAtoi`.

```
42
-42
1337
0
0
-2147483648
1
0
2147483647
-2147483648
0
```

## Notes

- The parsing must stop at the first non-digit character encountered after optional leading whitespace and sign. Trailing characters (including additional signs, letters, spaces, or another sign) must be ignored.
- The constant values are `INT_MIN = -2^31 = -2147483648` and `INT_MAX = 2^31 - 1 = 2147483647`. Clamping to this range is required when the parsed numeric value falls outside it.
- An empty string or a string with only whitespace/invalid characters (e.g., `"words and 987"`, `"0-1"`) should return `0`.
