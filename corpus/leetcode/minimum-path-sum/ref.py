import sys
import json

def solve(grid: list[list[int]]) -> int:
    if not grid or not grid[0]:
        return 0
    m, n = len(grid), len(grid[0])
    # Use rolling 1D dp array of size n
    dp = [0] * n
    for i in range(m):
        for j in range(n):
            v = grid[i][j]
            if i == 0 and j == 0:
                dp[j] = v
            elif i == 0:
                dp[j] = dp[j-1] + v
            elif j == 0:
                dp[j] = dp[j] + v
            else:
                dp[j] = min(dp[j], dp[j-1]) + v
    return dp[n-1]


CASES = [
    {
        "id": 0,
        "input": [
            [1, 3, 1],
            [1, 5, 1],
            [4, 2, 1],
        ],
    },
    {
        "id": 1,
        "input": [
            [1, 2],
            [3, 4],
        ],
    },
    {
        "id": 2,
        "input": [[0]],
    },
    {
        "id": 3,
        "input": [[5]],
    },
    {
        "id": 4,
        "input": [[1, 2, 3]],
    },
    {
        "id": 5,
        "input": [[7], [2], [5]],
    },
    {
        "id": 6,
        "input": [
            [1, 3, 1, 2],
            [1, 5, 1, 3],
            [4, 2, 1, 1],
            [2, 1, 3, 1],
        ],
    },
    {
        "id": 7,
        "input": [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ],
    },
]


if __name__ == '__main__':
    out = []
    for case in CASES:
        result = solve(case["input"])
        out.append({
            "id": case["id"],
            "input": case["input"],
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
