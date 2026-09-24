# Best Time to Buy and Sell Stock II

## Problem

You are given an integer array `prices` where `prices[i]` is the price of a stock on day `i`.

You may complete as many transactions as you like (buy one share, later sell it). However, at any time you may hold **at most one share** — meaning you must sell before you can buy again.

Return the **maximum profit** achievable.

## Function Signature

```
(solve prices)
  -> integer
```

- `prices` : `list[int]` — daily stock prices (length ≥ 1, prices ≥ 0).

## Input / Output Convention (Aura)

Input is provided as `CASE0=...` lines on a single string (stdin-less harness):

```
CASE0=prices=[7,1,5,3,6,4]
```

Output should be the integer answer:

```
OUTPUT=7
```

(Transactions: buy at 1, sell at 5 (+4); buy at 3, sell at 6 (+3); total = 7.)

## Examples

| Input | Output | Explanation |
|-------|--------|-------------|
| `CASE0=prices=[7,1,5,3,6,4]` | `7` | Two profitable trades as above. |
| `CASE0=prices=[1,2,3,4,5]` | `4` | Buy at 1, sell at 5. |
| `CASE0=prices=[7,6,4,3,1]` | `0` | No profitable trades; do nothing. |

## Notes

- The answer is always non-negative; a no-trade strategy yields `0`.
- An optimal strategy is equivalent to summing every upward day-to-day move: `max(0, prices[i] - prices[i-1])` across all `i`.
- Output only the integer, no additional text or formatting.
