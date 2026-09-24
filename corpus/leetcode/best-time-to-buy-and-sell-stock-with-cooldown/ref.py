def solve(prices):
    if not prices:
        return 0
    n = len(prices)
    if n == 1:
        return 0
    hold = -prices[0]
    free = 0
    cooldown = 0
    for i in range(1, n):
        new_hold = max(hold, free - prices[i])
        new_free = max(free, cooldown)
        new_cooldown = hold + prices[i]
        hold, free, cooldown = new_hold, new_free, new_cooldown
    return max(free, cooldown)


CASES = [
    {"prices": [1, 2, 3, 0, 2]},
    {"prices": [1]},
    {"prices": []},
    {"prices": [1, 2, 4]},
    {"prices": [2, 1, 4]},
    {"prices": [6, 1, 3, 2, 4, 7]},
    {"prices": [1, 2, 3, 4, 5]},
    {"prices": [5, 4, 3, 2, 1]},
]


if __name__ == '__main__':
    import json
    results = []
    for idx, case in enumerate(CASES):
        out = solve(**case)
        results.append({
            "id": idx,
            "input": case,
            "expected": json.dumps(out, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
