# Sqrt(x)

## Problem

Given a non-negative integer `x`, compute its integer square root — the largest integer `r` such that `r * r <= x`. You must not use any built-in square root or exponentiation function.

## Function Signature

```python
def solve(x: int) -> int:
    ...
```

## Input

The harness calls `solve(x)` directly. There is no stdin. Each case is configured in the harness as:

```
CASE0=x=0
CASE1=x=4
CASE2=x=8
CASE3=x=2147395599
```

(Each `CASEn=` line supplies the argument(s) for that test case; the function returns one integer.)

## Output

Return a single integer: the integer square root of `x`.

## Notes

- Use binary search on the range `[0, x]` (or a tighter upper bound) in `O(log x)` time.
- Be careful with mid-point overflow when `x` is large: compute `mid = left + (right - left) // 2` and compare `mid <= x // mid` instead of `mid * mid <= x`.
