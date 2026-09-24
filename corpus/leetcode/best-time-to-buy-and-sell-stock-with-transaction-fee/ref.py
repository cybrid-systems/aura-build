from typing import List

def solve(prices: List[int], fee: int) -> int:
    if not prices:
        return 0
    n = len(prices)
    # cash: max profit when not holding stock
    # hold: max profit when holding stock
    cash = 0
    hold = -prices[0]
    for i in range(1, n):
        prev_cash = cash
        # sell stock today
        cash = max(cash, hold + prices[i] - fee)
        # buy stock today
        hold = max(hold, prev_cash - prices[i])
    return cash

CASES = [
    {"prices": [1, 3, 2, 8, 4, 9], "fee": 2},
    {"prices": [1, 3, 7, 5, 10, 3], "fee": 3},
    {"prices": [1], "fee": 1},
    {"prices": [5, 5, 5, 5], "fee": 1},
    {"prices": [9, 8, 7, 6, 5, 4, 3, 2, 1], "fee": 0},
    {"prices": [1, 2, 3, 4, 5], "fee": 0},
    {"prices": [4, 5, 2, 3, 7, 1, 5], "fee": 2},
    {"prices": [0, 1, 0, 1, 0, 1], "fee": 1},
]

if __name__ == '__main__':
    import json
    out = []
    for i, c in enumerate(CASES):
        res = solve(c["prices"], c["fee"])
        out.append({"id": i, "input": c, "expected": json.dumps(res, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
