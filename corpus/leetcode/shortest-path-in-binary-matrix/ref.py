from collections import deque
from typing import List

def solve(grid: List[List[int]]) -> int:
    n = len(grid)
    if n == 0:
        return -1
    if grid[0][0] != 0 or grid[n-1][n-1] != 0:
        return -1
    if n == 1:
        return 1
    
    # 8-directional moves
    directions = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
    
    visited = [[False]*n for _ in range(n)]
    q = deque()
    q.append((0,0,1))  # row, col, distance (cells visited count)
    visited[0][0] = True
    
    while q:
        r, c, dist = q.popleft()
        if r == n-1 and c == n-1:
            return dist
        for dr, dc in directions:
            nr, nc = r+dr, c+dc
            if 0 <= nr < n and 0 <= nc < n and not visited[nr][nc] and grid[nr][nc] == 0:
                visited[nr][nc] = True
                q.append((nr, nc, dist+1))
    
    return -1


CASES = [
    {"grid": [[0,0,0],[1,1,0],[1,1,0]]},
    {"grid": [[0,1],[1,0]]},
    {"grid": [[1,0,0],[0,0,0],[0,0,1]]},
    {"grid": [[0]]},
    {"grid": [[1]]},
    {"grid": [[0,0,0,0],[0,1,1,0],[0,1,1,0],[0,0,0,0]]},
    {"grid": [[0,0],[0,0]]},
    {"grid": [[0,1,0],[1,0,1],[0,1,0]]},
]


if __name__ == '__main__':
    import json
    results = []
    for i, case in enumerate(CASES):
        out = solve(**case)
        results.append({"id": i, "input": case, "expected": json.dumps(out, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(results, ensure_ascii=False))
