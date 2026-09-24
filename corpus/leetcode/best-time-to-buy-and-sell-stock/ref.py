import json
import sys

def solve(prices: list[int]) -> int:
    if not prices:
        return 0
    min_price = prices[0]
    max_profit = 0
    for price in prices[1:]:
        if price < min_price:
            min_price = price
        else:
            profit = price - min_price
            if profit > max_profit:
                max_profit = profit
    return max_profit


CASES = [
    {"id": 0, "prices": [7, 1, 5, 3, 6, 4]},
    {"id": 1, "prices": [7, 6, 4, 3, 1]},
    {"id": 2, "prices": [1]},
    {"id": 3, "prices": [2, 4, 1]},
    {"id": 4, "prices": [3, 2, 6, 5, 0, 3]},
    {"id": 5, "prices": [1, 2, 3, 4, 5]},
    {"id": 6, "prices": [5, 4, 3, 2, 1]},
    {"id": 7, "prices": [0, 0, 0, 0]},
]


if __name__ == '__main__':
    results = []
    for case in CASES:
        inp = {k: v for k, v in case.items() if k != "id"}
        expected = solve(case["prices"])
        results.append({
            "id": case["id"],
            "input": inp,
            "expected": json.dumps(expected, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
