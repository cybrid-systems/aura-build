# Best Time to Buy and Sell Stock

## Problem

You are given an array `prices` where `prices[i]` is the price of a given stock on day `i`.

You want to maximize your profit by choosing a **single** day to buy and a **different** day in the future to sell.

Return the maximum profit you can achieve from this transaction. If no profit is possible, return `0`.

## Function Signature

```python
def solve(prices: list[int]) -> int:
    ...
```

## Input

The harness will read from standard input in the following format. There are no arguments passed to `solve` directly — the first line is the test case count.

```
CASE0=<count>
CASE0.lines[0] = <comma-separated integers, e.g. "7,1,5,3,6,4">
```

- `CASE0` indicates there is a single test block (index 0).
- The integer after `CASE0=` is the number of lines that follow (typically `1` for this problem, since the whole array is on one line).
- Each subsequent line contains the comma-separated prices for that test case.

For example:

```
CASE0=1
7,1,5,3,6,4
```

expects `solve([7, 1, 5, 3, 6, 4])` to be evaluated.

## Output

Your `solve` function should return an `int` — the maximum achievable profit.

## Constraints

- `1 <= prices.length <= 10^5`
- `0 <= prices[i] <= 10^4`

## Examples

**Example 1**
- Input: `[7, 1, 5, 3, 6, 4]`
- Output: `5`
- Explanation: Buy on day 2 (price = 1), sell on day 5 (price = 6), profit = 6 - 1 = 5.

**Example 2**
- Input: `[7, 6, 4, 3, 1]`
- Output: `0`
- Explanation: Prices never rise, so no profitable transaction. Return `0`.

## Notes

- You must buy **before** you sell (sell day index > buy day index).
- The naive O(n²) approach will be too slow for the maximum input size — aim for a single-pass O(n) solution.
- The harness will call `solve` once per test case line and compare the returned integer against the expected answer.
