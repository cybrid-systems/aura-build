# Coin Change

## Problem

You are given `n` coin denominations with positive integer values and a target amount `amount`. Each denomination may be used an unlimited number of times. Determine the minimum number of coins whose values sum exactly to `amount`. If it is not possible to form the amount, report that no solution exists.

## Function Signature

```clojure
(solve [denominations amount] ...)
```

- `denominations` — vector of positive integers (coin values)
- `amount` — non-negative integer (target sum)
- Returns the minimum number of coins needed, or a sentinel (e.g. `-1`) if the amount cannot be formed.

## Input / Output Convention

The harness invokes the solver with zero stdin; arguments are supplied via the `CASE0`/`CASE1`/... environment lines as space-separated values. The first number on the line is treated as the amount, followed by the list of denominations.

Examples:

```
CASE0=11 1 2 5
CASE1=3 2
CASE2=0 1 2 5
```

Expected outputs (minimum coin count):

```
CASE0=3     ; 11 = 5 + 5 + 1
CASE1=-1    ; 3 cannot be formed from {2}
CASE2=0     ; amount 0 needs no coins
```

## Notes

- The standard 1-D dynamic programming recurrence `dp[i] = min(dp[i], dp[i - d] + 1)` over `i = d..amount` yields an `O(n * amount)` solution.
- `amount = 0` should return `0` coins (empty selection), not a failure.
- If any denomination equals `1`, every non-negative amount is reachable, so a failure result (`-1`) is only possible when `amount > 0` and no denomination can contribute.
