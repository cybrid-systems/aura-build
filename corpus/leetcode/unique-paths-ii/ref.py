MOD = 1000000007

def count_paths(grid):
    m = len(grid)
    if m == 0:
        return 0
    n = len(grid[0])
    if n == 0:
        return 0
    if grid[0][0] == 1 or grid[m-1][n-1] == 1:
        return 0
    # dp is 1D rolling array, length n
    dp = [0] * n
    dp[0] = 1
    for i in range(m):
        for j in range(n):
            if grid[i][j] == 1:
                dp[j] = 0
            else:
                if j > 0:
                    dp[j] = (dp[j] + dp[j-1]) % MOD
    return dp[n-1]

def solve(grids):
    return [count_paths(g) for g in grids]

CASES = [
    {"grid": [[0,0,0],[0,1,0],[0,0,0]]},
    {"grid": [[0,1],[0,0]]},
    {"grid": [[1]]},
    {"grid": [[0]]},
    {"grid": [[0,0],[1,0],[0,0]]},
    {"grid": [[0,0,0,0],[0,0,0,0]]},
    {"grid": [[1,0],[0,0]]},
    {"grid": [[0,0],[0,1]]},
]

if __name__ == '__main__':
    import json
    out = []
    for i, case in enumerate(CASES):
        result = solve([case["grid"]])
        out.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result[0], separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
