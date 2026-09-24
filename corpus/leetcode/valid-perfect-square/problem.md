# Valid Perfect Square

Given a positive integer `n`, determine whether it is a perfect square — i.e., whether there exists an integer `x` such that `x * x == n`. You may not use any built-in square-root function or exponentiation operator.

## Function signature

```
(solve n)
```

- `n` — a positive integer (`1 <= n <= 2^31 - 1`).

Return truthy when `n` is a perfect square, otherwise falsy.

## Input / Output

There is no stdin. Inside the Aura harness the case is provided as a single line of the form:

```
CASE0=<n>
```

where `<n>` is the positive integer to test. Your `solve` function receives `n` and must return the answer for that single case.

Examples (illustrative, not exhaustive):

- `CASE0=16` → truthy (4 × 4 = 16)
- `CASE0=14` → falsy
- `CASE0=1`  → truthy
- `CASE0=2147483647` → falsy

## Notes

- Use binary search on the range `[1, n]` (or `[0, n]` if you prefer) to find the integer square root. Be careful with mid-multiplication: use `mid <= n / mid` to avoid 32-bit overflow when `n` is near `2^31 - 1`.
- Edge cases to consider: `n == 0` (handled by the lower bound) and `n == 1` (the only perfect square in `[0, 1]` with both bounds checked).
