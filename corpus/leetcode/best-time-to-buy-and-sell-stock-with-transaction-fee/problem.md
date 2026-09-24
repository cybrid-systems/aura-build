# Best Time to Buy and Sell Stock with Transaction Fee

## Problem

You are given an array `prices` where `prices[i]` is the price of a stock on day `i`, and an integer `fee` representing the transaction fee charged for each completed buy-sell pair (the fee is paid once per transaction, when the stock is sold).

You may complete as many transactions as you like, but at any time you may hold at most one share of the stock (i.e., you must sell before buying again). Returns from short selling are not allowed.

Determine the maximum profit achievable.

## Function Signature

```clojure
(defn solve [prices fee] ...)
```

## Input

The harness invokes `solve` directly with the parsed arguments. There is no stdin. Test cases are presented as `CASE0=...` lines for documentation only; your function receives the values as arguments.

- `prices`: a vector of integers (length >= 1)
- `fee`: a non-negative integer

## Output

Return a single integer: the maximum possible profit.

## Notes

- A transaction consists of one buy followed by one sell; the fee `fee` is subtracted from the profit exactly once per completed transaction (typically when selling).
- You are not required to perform any transactions if it is not profitable.
- The answer fits in a standard 32-bit signed integer for the given constraints.
