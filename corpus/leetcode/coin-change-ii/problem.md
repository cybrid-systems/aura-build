# Coin Change II

Given an integer `amount` and a list of distinct positive-integer coin denominations `coins`, count the number of **combinations** of coins whose values sum exactly to `amount`. Two combinations are considered the same if they contain the same coins with the same multiplicities, regardless of order.

## Function Signature

```lisp
(defun solve (amount coins)
  ...)
```

- `amount` — a non-negative integer.
- `coins` — a list of distinct positive integers (you may assume it is sorted ascending).

Return a single non-negative integer: the number of combinations.

## Input / Output Convention

The harness reads no stdin; the test harness invokes `solve` directly with literal case arguments and prints the result. Each case is shown below in the form used by the verifier's `CASE0=...` lines:

```
CASE0=(solve 5 '(1 2 5))
CASE1=(solve 3 '(2)
CASE2=(solve 10 '(1 5 10 25)
CASE3=(solve 0 '(1 2 5)
CASE4=(solve 100 '(1 5 10 25 50)
```

Expected counts for the cases above:

| Case | Combination Count |
|------|-------------------|
| 0    | 4                 |
| 1    | 0                 |
| 2    | 4                 |
| 3    | 1                 |
| 4    | 292               |

## Notes

- Order does not matter: `1+2+2` is the same combination as `2+2+1`.
- The standard 1-D DP iterating over coin denominations first naturally avoids counting permutations.
- `amount = 0` has exactly **one** combination (the empty combination) regardless of `coins`.
- Integer counts may fit in a standard 64-bit integer for the given ranges; no modular arithmetic is required.
