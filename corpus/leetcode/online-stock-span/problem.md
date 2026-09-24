# Online Stock Span

For each trading day, the "span" of the day's stock price is the number of consecutive days (going backwards from today, including today) for which the stock price was **less than or equal** to today's price. Given a sequence of daily stock prices, compute the span for every day.

## Input

The input is read line by line from standard input.

- Line 1: an integer `n` — the number of trading days (1 ≤ n ≤ 10^5).
- Line 2: `n` space-separated integers — the daily prices (each between 0 and 10^9).

## Output

Print `n` space-separated integers: the span of each day, in the same order as the input prices.

## Example

Input:
```
6
100 80 60 70 60 75
```

Explanation of spans:

| Day | Price | Span |
|-----|-------|------|
| 1   | 100   | 1    |
| 2   | 80    | 1    |
| 3   | 60    | 1    |
| 4   | 70    | 2    |
| 5   | 60    | 1    |
| 6   | 75    | 4    |

Output:
```
1 1 1 2 1 4
```

## Function Signature

```python
def solve(prices: list[int]) -> list[int]:
    ...
```

## Notes

- Use a **monotonic decreasing stack** storing pairs of `(price, span)` to achieve O(n) time.
- Today's span is 1 plus the accumulated span of the most recent day whose price is strictly greater than today's price.
