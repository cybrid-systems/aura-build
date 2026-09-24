def solve(prices):
    if not prices:
        return 0
    n = len(prices)
    # left[i] = max profit from 0..i using at most 1 transaction
    left = [0] * n
    min_price = prices[0]
    for i in range(1, n):
        min_price = min(min_price, prices[i])
        left[i] = max(left[i-1], prices[i] - min_price)
    # right[i] = max profit from i..n-1 using at most 1 transaction
    right = [0] * n
    max_price = prices[-1]
    for i in range(n-2, -1, -1):
        max_price = max(max_price, prices[i])
        right[i] = max(right[i+1], max_price - prices[i])
    best = 0
    for i in range(n):
        best = max(best, left[i] + right[i])
    return best


CASES = [
    {"prices": []},
    {"prices": [5]},
    {"prices": [5, 5, 5, 5]},
    {"prices": [1, 2, 3, 4, 5]},
    {"prices": [5, 4, 3, 2, 1]},
    {"prices": [3, 3, 5, 0, 0, 3, 1, 4]},
    {"prices": [1, 2, 4, 2, 5, 7, 2, 4, 9, 0]},
    {"prices": [7, 6, 4, 3, 1]},
    {"prices": [1, 2, 1, 2, 1, 2]},
    {"prices": [6, 1, 3, 2, 4, 7]},
]


if __name__ == '__main__':
    import json
    results = []
    for idx, case in enumerate(CASES):
        out = solve(**case)
        results.append({
            "id": idx,
            "input": case,
            "expected": json.dumps(out, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
