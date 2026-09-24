def solve(p):
    n = len(p)
    if n <= 2:
        return 0
    dp = [[0] * n for _ in range(n)]
    for length in range(2, n):
        for i in range(n - length):
            j = i + length
            dp[i][j] = float('inf')
            for k in range(i, j):
                cost = dp[i][k] + dp[k + 1][j] + p[i - 1] * p[k] * p[j] if i > 0 else dp[i][k] + dp[k + 1][j] + p[i] * p[k] * p[j]
                if cost < dp[i][j]:
                    dp[i][j] = cost
    return dp[0][n - 1]


CASES = [
    {"p": [1, 2]},
    {"p": [10, 30]},
    {"p": [10, 30, 5]},
    {"p": [30, 35, 15, 5, 10, 20, 25]},
    {"p": [40, 20, 30, 10, 30]},
    {"p": [1, 2, 3, 4, 5]},
    {"p": [5, 10, 3, 12, 5, 50, 6]},
    {"p": list(range(1, 101))},
]


if __name__ == '__main__':
    import json
    results = []
    for i, case in enumerate(CASES):
        ans = solve(case["p"])
        results.append({"id": i, "input": case, "expected": json.dumps(ans, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
