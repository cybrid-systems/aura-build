def solve(denominations, amount):
    if amount == 0:
        return 0
    if not denominations:
        return -1
    max_val = amount + 1
    dp = [max_val] * (amount + 1)
    dp[0] = 0
    for i in range(1, amount + 1):
        for d in denominations:
            if d <= i and dp[i - d] + 1 < dp[i]:
                dp[i] = dp[i - d] + 1
    return dp[amount] if dp[amount] != max_val else -1


CASES = [
    {"denominations": [1, 2, 5], "amount": 11},
    {"denominations": [2], "amount": 3},
    {"denominations": [1, 2, 5], "amount": 0},
    {"denominations": [1], "amount": 1},
    {"denominations": [5, 10, 25], "amount": 30},
    {"denominations": [3, 7], "amount": 14},
    {"denominations": [2, 5, 10], "amount": 1},
    {"denominations": [1, 3, 4], "amount": 6},
]

if __name__ == '__main__':
    import json
    out = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        out.append({"id": i, "input": case, "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
