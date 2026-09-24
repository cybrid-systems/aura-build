# Perfect Squares

## Problem

Given a positive integer `n`, find the **minimum number of perfect square numbers** (1, 4, 9, 16, 25, ...) whose sum equals `n`.

For example:
- `n = 12` can be written as `4 + 4 + 4`, so the answer is `3`.
- `n = 13` can be written as `4 + 9`, so the answer is `2`.
- `n = 1` is itself a perfect square, so the answer is `1`.

Your task is to compute this minimum count for any given `n`.

## Function Signature

```python
def solve(n: int) -> int:
    ...
```

## Input / Output Convention

The harness invokes your function directly with no stdin. Each test case is run as:

```
CASE0=n=<value>
```

Lines beginning with `CASE0=` (and further `CASE1=`, ...) describe the arguments passed to `solve`. Your function must return the minimal number of perfect squares summing to `n`.

Example:

```
CASE0=n=12
CASE1=n=13
CASE2=n=1
```

Expected returns: `3`, `2`, `1`.

## Notes

- `n` is a non-negative integer (`0 ≤ n ≤ 10^4` in the visible tests; your solution should be efficient up to at least `n = 10^4`, ideally higher).
- The greedy approach of always subtracting the largest square is **not** always correct (e.g., for `n = 12` greedy gives `9 + 1 + 1 + 1 = 4`, but the optimal is `4 + 4 + 4 = 3`). Use dynamic programming or number-theoretic reasoning instead.
- By Lagrange's four-square theorem, every non-negative integer can be expressed as the sum of at most 4 perfect squares, so the answer is always between `1` and `4` for `n > 0` (and `0` for `n = 0`).
