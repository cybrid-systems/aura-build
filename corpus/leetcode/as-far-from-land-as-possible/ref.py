import json
from collections import deque
from typing import List

def solve(grid: List[List[int]]) -> int:
    n = len(grid)
    if n == 0:
        return -1
    
    # Count land and water
    land_count = 0
    water_count = 0
    queue = deque()
    
    for i in range(n):
        for j in range(n):
            if grid[i][j] == 1:
                land_count += 1
                queue.append((i, j, 0))
            else:
                water_count += 1
    
    # Edge cases: all land or all water
    if land_count == 0 or water_count == 0:
        return -1
    
    # BFS from all land cells
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    max_dist = 0
    
    while queue:
        i, j, dist = queue.popleft()
        max_dist = max(max_dist, dist)
        for di, dj in directions:
            ni, nj = i + di, j + dj
            if 0 <= ni < n and 0 <= nj < n and grid[ni][nj] == 0:
                grid[ni][nj] = dist + 1  # mark as visited
                queue.append((ni, nj, dist + 1))
    
    return max_dist

CASES = [
    {"id": 0, "input": {"grid": [[1,0,1],[0,0,0],[1,0,1]]}},
    {"id": 1, "input": {"grid": [[1,0,0],[0,0,0],[0,0,0]]}},
    {"id": 2, "input": {"grid": [[1,1,1],[1,1,1],[1,1,1]]}},
    {"id": 3, "input": {"grid": [[0,0,0],[0,0,0],[0,0,0]]}},
    {"id": 4, "input": {"grid": [[1,0,1,0,1],[0,0,0,0,0],[1,0,1,0,1],[0,0,0,0,0],[1,0,1,0,1]]}},
    {"id": 5, "input": {"grid": [[0,0,0,0],[0,1,1,0],[0,1,1,0],[0,0,0,0]]}},
    {"id": 6, "input": {"grid": [[1]]}},
    {"id": 7, "input": {"grid": [[0]]}},
]

if __name__ == '__main__':
    results = []
    for case in CASES:
        # Deep copy to avoid mutating case data
        grid_input = [row[:] for row in case["input"]["grid"]]
        result = solve(grid_input)
        results.append({
            "id": case["id"],
            "input": case["input"],
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
