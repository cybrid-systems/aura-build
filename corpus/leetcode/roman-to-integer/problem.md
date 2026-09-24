# Roman to Integer

## Problem Statement

Given a string `s` representing a Roman numeral, return the integer value it denotes.

Roman numerals use seven symbols with the following fixed values:

| Symbol | Value |
|--------|-------|
| I      | 1     |
| V      | 5     |
| X      | 10    |
| L      | 50    |
| C      | 100   |
| D      | 500   |
| M      | 1000  |

Numerals are written from largest to smallest (left to right), and the values are summed — except when a smaller value appears immediately before a larger one, in which case it is subtracted (the subtractive form). The standard subtractive pairs are:

- `IV` → 4, `IX` → 9
- `XL` → 40, `XC` → 90
- `CD` → 400, `CM` → 900

The input is guaranteed to be a valid Roman numeral in the range `[1, 3999]`.

## Function Signature

```python
def solve(s: str) -> int:
    ...
```

## Input / Output Convention

The harness invokes `solve()` directly. There is no `stdin`; instead, the case is selected by environment variables and communicated through `CASE0`, `CASE1`, … lines, each of the form:

```
CASE0=s="III"
CASE1=s="LVIII"
CASE2=s="MCMXCIV"
```

Each `CASEn` line is parsed and the variable bindings it describes are passed to `solve()` as keyword arguments. Your function must return the integer result; the harness compares it against the expected answer.

## Examples

| Input `s`    | Output | Explanation                                  |
|--------------|--------|----------------------------------------------|
| `"III"`      | 3      | `I + I + I`                                  |
| `"LVIII"`    | 58     | `L (50) + V (5) + III (3)`                   |
| `"MCMXCIV"`  | 1994   | `M (1000) + CM (900) + XC (90) + IV (4)`     |

## Notes

- Assume `s` is non-empty and well-formed; no need to validate.
- A single left-to-right pass that compares each symbol's value to the next one is sufficient: subtract when the current value is smaller than the next, otherwise add.
