# Best Time to Buy and Sell Stock IV

## Problem

You are given an integer array `prices` where `prices[i]` is the price of a stock on day `i`, and an integer `k` representing the maximum number of transactions allowed.

A transaction consists of **buying** one share and later **selling** it. You may complete **at most `k`** transactions. After selling a stock, you may buy another stock later (i.e., you cannot hold more than one share at any time).

Determine the **maximum profit** you can achieve.

## Function Signature

```clojure
(solve prices k)
```

- `prices` — a vector of integers (the price on each day). Length `n` where `0 <= n <= 10^3` (or larger for the `n^2` DP variant).
- `k` — a non-negative integer (maximum allowed transactions).

Return the maximum achievable profit as an integer.

## I/O Convention (Aura harness)

The harness invokes `(solve prices k)` directly. When a driver is present, the stdin/stdout convention uses the following format:

```
CASE0=10
prices=[2,4,1,7,5,3,6,4]
k=2
CASE0=7
```

- `CASE0=...` on the first line indicates the answer expected for the test case that follows.
- Subsequent lines describe inputs (vector literals use `[..]`, scalars are `name=value`).
- Output is one integer per case: the maximum profit.
- An empty `prices` (or `k == 0`) yields `0`.

## Notes

- If `k` is large (e.g., `k >= n/2`), the problem reduces to the unbounded "as many transactions as you like" variant, which can be solved greedily by summing all positive price differences.
- A common approach uses DP with two states per transaction count: `hold[i][j]` (max profit ending with a share on day `i` using `j` transactions) and `cash[i][j]` (max profit ending without a share on day `i` using `j` transactions). The space can be reduced to two rolling rows.
- Watch out for the edge case `k == 0` and empty input — both must return `0`.
