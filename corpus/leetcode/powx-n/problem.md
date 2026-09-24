# Pow(x, n)

## Problem

Implement `pow(x, n)`, which computes `x` raised to the power `n` (i.e., `x^n`).

You are given a floating-point base `x` and an integer exponent `n`. Implement an efficient solution using **fast exponentiation** (binary exponentiation), and handle negative exponents correctly by computing the reciprocal when needed.

```
pow(2.0, 10)  = 1024.0
pow(2.1, 3)   = 9.261
pow(2.0, -2)  = 0.25
```

Constraints:
- `-100.0 < x < 100.0`
- `-2^31 <= n <= 2^31 - 1`
- `x` is a floating-point number; the result should be accurate to within `1e-5` of the true value.

## Function Signature

```python
def solve(x: float, n: int) -> float:
    ...
```

## Input / Output (Harness Convention)

The problem is exposed to the solver as a set of zero-argument cases read from standard input. Each case contains two values on a single line: the base `x` and the integer exponent `n`. The harness will invoke `solve(x, n)` for each case and print the returned value.

Example input:

```
CASE0=2.0 10
CASE1=2.1 3
CASE2=2.0 -2
CASE3=1.0 0
```

Example output (values printed with sufficient decimal precision):

```
1024.0
9.261000000000001
0.25
1.0
```

## Notes

- Use **iterative binary exponentiation** to achieve `O(log |n|)` time complexity; avoid the naive `O(|n|)` repeated multiplication.
- Remember the special case: any number to the power `0` equals `1` (including `0.0^0`, which by convention here is `1.0`).
- For negative `n`, compute `pow(x, -n)` and take the reciprocal: `1 / pow(x, -n)`.
- Be mindful of the exponent range — `n` can equal `INT_MIN` (`-2^31`), where `-n` overflows a signed 32-bit int. Handle this by converting to a 64-bit integer (or working with `n` as a Python `int`, which is unbounded).
- Absolute error tolerance is `1e-5`.
