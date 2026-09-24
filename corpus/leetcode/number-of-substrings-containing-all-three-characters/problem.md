# Number of Substrings Containing All Three Characters

## Problem

Given a string `s` consisting only of the characters `'a'`, `'b'`, and `'c'`, count the number of substrings that contain **at least one** `'a'`, **at least one** `'b'`, and **at least one** `'c'`.

Return the total count.

## Function Signature

```python
def solve(s: str) -> int:
    ...
```

## Input

A single line read from standard input containing the string `s`.

## Output

A single integer: the number of substrings of `s` that contain all three characters `'a'`, `'b'`, and `'c'`.

## I/O Convention (Harness Format)

The harness supplies the input on stdin in the following form:

```
CASE0=aababc
```

Your `solve` function receives the raw value after `CASE0=` (i.e. `aababc`), and should return the answer as an `int`, which the harness will print.

## Examples

- `s = "abc"` → `1` (only `"abc"` itself contains all three)
- `s = "aaab"` → `0` (no `'c'` present)
- `s = "aababc"` → substrings containing all three: `"abab"`, `"ababc"`, `"bab"`, `"babc"`, `"abc"` → `5`

## Notes

- Use a sliding window: for each right endpoint, find the smallest left endpoint whose window still contains all three characters; then every longer window ending at the same right endpoint is also valid.
- Length of `s` can be large (up to 10⁵ or more); an O(n) solution is expected.
- The string contains only `'a'`, `'b'`, `'c'`, but your solution should not assume this beyond recognizing these three characters.
