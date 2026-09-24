from collections import deque
import json
import sys

def solve(grid):
    if not grid or not grid[0]:
        return
    m, n = len(grid), len(grid[0])
    INF = 2147483647
    q = deque()
    for i in range(m):
        for j in range(n):
            if grid[i][j] == 0:
                q.append((i, j))
    while q:
        i, j = q.popleft()
        d = grid[i][j] + 1
        for di, dj in ((1,0),(-1,0),(0,1),(0,-1)):
            ni, nj = i+di, j+dj
            if 0 <= ni < m and 0 <= nj < n and grid[ni][nj] == INF:
                grid[ni][nj] = d
                q.append((ni, nj))

CASES = [
    {"id": 0, "grid": [[-1,0,2147483647],[2147483647,2147483647,2147483647],[0,2147483647,-1]]},
    {"id": 1, "grid": [[0]]},
    {"id": 2, "grid": [[-1]]},
    {"id": 3, "grid": [[2147483647,2147483647],[2147483647,2147483647]]},
    {"id": 4, "grid": [[0,2147483647],[-1,2147483647]]},
    {"id": 5, "grid": [[0,-1],[2147483647,2147483647]]},
    {"id": 6, "grid": [[2147483647,0,2147483647,-1],[2147483647,2147483647,2147483647,2147483647]]},
    {"id": 7, "grid": [[0,2147483647,0],[2147483647,2147483647,2147483647],[0,2147483647,0]]},
]

if __name__ == '__main__':
    out = []
    for c in CASES:
        g = [row[:] for row in c["grid"]]
        solve(g)
        out.append({"id": c["id"], "input": {"grid": c["grid"]}, "expected": json.dumps(g, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(out, ensure_ascii=False))
