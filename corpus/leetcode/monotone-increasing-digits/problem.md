# Monotone Increasing Digits

## Problem

A non-negative integer is *monotone increasing* if its decimal digits, read from left to right, are non-decreasing (each next digit is greater than or equal to the previous one). For example, `7`, `123`, `111`, `134468` are monotone increasing, while `100`, `321`, `33457` are not.

Given a non-negative integer `N`, find the largest monotone increasing integer that is less than or equal to `N`.

## Function Signature

```python
def solve(N: int) -> int:
    ...
```

## Input / Output Convention

The harness calls `solve(N)` directly with a single integer argument and prints the returned integer. There is no stdin.

Example exchange shown to the harness:

```
CASE0=332
ANS0=299
CASE1=100
ANS1=99
CASE2=0
ANS2=0
```

## Notes

- `N` may be `0`; in that case the answer is `0`.
- Leading zeros are not produced — the returned value should be the actual integer (e.g., for `N = 100` the answer is `99`, not `099`).
- A single greedy pass from left to right, fixing any violation by decrementing and zeroing trailing digits, is sufficient.
