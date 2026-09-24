import sys
import json

def solve(m, n, grid):
    if m == 0 or n == 0:
        return 0
    max_side = 0
    dp = [0] * (n + 1)
    for i in range(1, m + 1):
        prev = 0
        for j in range(1, n + 1):
            temp = dp[j]
            if grid[i - 1][j - 1] == 1:
                dp[j] = min(dp[j], dp[j - 1], prev) + 1
                if dp[j] > max_side:
                    max_side = dp[j]
            else:
                dp[j] = 0
            prev = temp
    return max_side * max_side

CASES = [
    {
        "m": 4,
        "n": 5,
        "grid": [[1,0,1,0,0],[1,0,1,1,1],[1,1,1,1,1],[1,0,0,1,0]]
    },
    {
        "m": 1,
        "n": 1,
        "grid": [[0]]
    },
    {
        "m": 1,
        "n": 1,
        "grid": [[1]]
    },
    {
        "m": 2,
        "n": 2,
        "grid": [[1,1],[1,1]]
    },
    {
        "m": 3,
        "n": 3,
        "grid": [[0,0,0],[0,0,0],[0,0,0]]
    },
    {
        "m": 3,
        "n": 3,
        "grid": [[1,1,1],[1,1,1],[1,1,1]]
    },
    {
        "m": 5,
        "n": 5,
        "grid": [[1,0,1,1,1],[1,1,1,1,1],[1,1,1,1,1],[1,0,0,1,0],[1,1,1,1,1]]
    },
    {
        "m": 4,
        "n": 4,
        "grid": [[1,1,0,1],[1,1,1,1],[1,1,1,1],[0,1,1,1]]
    }
]

if __name__ == '__main__':
    results = []
    for idx, case in enumerate(CASES):
        out = solve(case["m"], case["n"], case["grid"])
        results.append({
            "id": idx,
            "input": {
                "m": case["m"],
                "n": case["n"],
                "grid": case["grid"]
            },
            "expected": json.dumps(out, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
