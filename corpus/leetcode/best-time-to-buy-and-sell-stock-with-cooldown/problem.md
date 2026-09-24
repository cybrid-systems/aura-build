# Best Time to Buy and Sell Stock with Cooldown

## Problem

You are given an array `prices` where `prices[i]` is the price of a given stock on day `i`. You may complete as many transactions as you like (i.e., buy one and sell one share of the stock multiple times) with the following rules:

- You may not engage in multiple transactions simultaneously (i.e., you must sell the stock before you buy again).
- After you sell your stock, you cannot buy stock on the next day (i.e., there is a **cooldown** of one day).

Return the **maximum profit** you can achieve.

## Function Signature

```python
def solve(prices: list[int]) -> int:
    ...
```

## Input/Output Convention

Input is supplied via global variables (no stdin), and output via the return value (no stdout).

- Input globals: `prices` (a list of integers, length `n` with `1 <= n <= 5000`, each `0 <= prices[i] <= 10000`)
- Output: an integer — the maximum achievable profit

### Example Case

`CASE0=prices=[1,2,3,0,2]` → `3`

Explanation: buy on day 0 (price 1), sell on day 1 (price 2), cooldown on day 2, buy on day 3 (price 0), sell on day 4 (price 2). Profit = (2−1) + (2−0) = 3.

## Notes

- If no profit is possible, return `0`.
- The cooldown only applies after a *sell*, not after a buy. You may buy on the day immediately following a buy's sell only if you skip one day (cooldown).
- A common approach uses dynamic programming with states representing "holding a stock," "not holding and ready to buy," and "in cooldown" — achievable in O(n) time and O(1) space.
