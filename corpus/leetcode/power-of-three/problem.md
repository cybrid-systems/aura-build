# Power of Three

## Problem

Given a non-negative integer `n`, determine whether it is a power of three. In other words, check if there exists an integer `k >= 0` such that `n == 3^k`.

Return `True` if `n` is a power of three, and `False` otherwise.

The integer `0` is **not** considered a power of three.

## Function Signature

```python
def solve(n: int) -> bool:
    ...
```

A `solve` function must accept one integer and return a boolean result.

## Input/Output (Case-Driven Convention)

The harness reads a single positive integer `t` giving the number of **cases** on the first line. Then `t` lines follow, each containing one integer `n`.

For each case, output a single line with `True` if `n` is a power of three, otherwise `False`.

### Format

```
CASE0=<n0>
CASE1=<n1>
...
```

Each `CASEi` line is a self-contained test: feed its `ni` value to `solve` and emit one boolean per line, in the same order as the cases.

## Examples

```
CASE0=27
CASE1=0
CASE2=45
```

Expected output:

```
True
False
False
```

## Notes

- The naive approach uses repeated division by 3 until the value reaches 1.
- An elegant O(1) trick uses modular arithmetic: for the 32-bit signed range, the maximum power of three is `3^19 = 1162261467`, and any valid power of three divides this number exactly. This requires the bound on `n` to be known and is not safe for arbitrary 64-bit inputs.
- Watch the edge case `n <= 0` carefully — these must always return `False`.
