def solve(amount, coins):
    # 1-D DP: for each coin, update dp[v] for v from coin to amount
    dp = [0] * (amount + 1)
    dp[0] = 1
    for c in coins:
        if c > amount:
            continue
        for v in range(c, amount + 1):
            dp[v] += dp[v - c]
    return dp[amount]


CASES = [
    {"amount": 5,  "coins": [1, 2, 5]},
    {"amount": 3,  "coins": [2]},
    {"amount": 10, "coins": [1, 5, 10, 25]},
    {"amount": 0,  "coins": [1, 2, 5]},
    {"amount": 100,"coins": [1, 5, 10, 25, 50]},
    {"amount": 0,  "coins": []},
    {"amount": 7,  "coins": [2, 3]},
    {"amount": 4,  "coins": [1, 2, 3]},
]


if __name__ == '__main__':
    import json
    out = []
    for i, c in enumerate(CASES):
        res = solve(c["amount"], c["coins"])
        out.append({
            "id": i,
            "input": {"amount": c["amount"], "coins": c["coins"]},
            "expected": json.dumps(res, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
