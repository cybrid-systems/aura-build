import json, sys
from typing import List

def solve(grid: List[List[int]]) -> int:
    m = len(grid)
    if m == 0:
        return 1
    n = len(grid[0])
    if n == 0:
        return 1
    # dp[i][j] = min health needed entering cell (i,j)
    # We'll compute from bottom-right to top-left.
    INF = 10**18
    dp = [[INF]*n for _ in range(m)]
    # base case: from (m-1,n-1) we just need > 0 after applying effect
    dp[m-1][n-1] = max(1, 1 - grid[m-1][n-1])
    # last row
    for j in range(n-2, -1, -1):
        need = dp[m-1][j+1] - grid[m-1][j]
        dp[m-1][j] = max(1, need)
    # last column
    for i in range(m-2, -1, -1):
        need = dp[i+1][n-1] - grid[i][n-1]
        dp[i][n-1] = max(1, need)
    # fill rest
    for i in range(m-2, -1, -1):
        for j in range(n-2, -1, -1):
            min_next = min(dp[i+1][j], dp[i][j+1])
            need = min_next - grid[i][j]
            dp[i][j] = max(1, need)
    return dp[0][0]

CASES = [
    {"grid": [[-2,-3,3],[-5,-10,1],[10,30,-5]]},
    {"grid": [[0]]},
    {"grid": [[-3]]},
    {"grid": [[1,2,3],[0,0,0]]},
    {"grid": [[-1,-1,-1],[-1,-1,-1],[-1,-1,-1]]},
    {"grid": [[100]]},
    {"grid": [[0,0,0],[0,0,0]]},
    {"grid": [[-2,1],[-3,1]]},
]

if __name__ == '__main__':
    out = []
    for i, c in enumerate(CASES):
        result = solve(c["grid"])
        out.append({"id": i, "input": {"grid": c["grid"]}, "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
