import json

def solve(prices):
    profit = 0
    for i in range(1, len(prices)):
        diff = prices[i] - prices[i - 1]
        if diff > 0:
            profit += diff
    return profit

CASES = [
    {"prices": [7, 1, 5, 3, 6, 4]},
    {"prices": [1, 2, 3, 4, 5]},
    {"prices": [7, 6, 4, 3, 1]},
    {"prices": [5]},
    {"prices": [5, 5, 5, 5]},
    {"prices": [0, 1, 2, 0, 1, 2]},
    {"prices": [1, 0]},
    {"prices": [3, 2, 1, 2, 3, 0, 4]},
]

if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        out = solve(case["prices"])
        results.append({
            "id": i,
            "input": {"prices": case["prices"]},
            "expected": json.dumps(out, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
