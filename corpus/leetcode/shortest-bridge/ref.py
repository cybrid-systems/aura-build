import sys
from collections import deque
import json


def solve(grid: list[list[int]]) -> int:
    n = len(grid)
    if n == 0:
        return 0

    visited = [[False] * n for _ in range(n)]
    island_cells = []

    # Find first island using DFS
    def dfs(i, j):
        if i < 0 or i >= n or j < 0 or j >= n:
            return
        if grid[i][j] == 0 or visited[i][j]:
            return
        visited[i][j] = True
        island_cells.append((i, j))
        dfs(i + 1, j)
        dfs(i - 1, j)
        dfs(i, j + 1)
        dfs(i, j - 1)

    found = False
    for i in range(n):
        for j in range(n):
            if grid[i][j] == 1 and not found:
                dfs(i, j)
                found = True
                break
        if found:
            break

    # Multi-source BFS from first island
    queue = deque()
    dist = [[-1] * n for _ in range(n)]

    for (i, j) in island_cells:
        queue.append((i, j))
        dist[i][j] = 0

    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]

    while queue:
        i, j = queue.popleft()
        # If we reached the second island (a 1 that is not in island_cells)
        if grid[i][j] == 1 and (i, j) not in [(x, y) for x, y in island_cells]:
            # This shouldn't happen on first pop, but check neighbors instead
            pass
        for di, dj in directions:
            ni, nj = i + di, j + dj
            if 0 <= ni < n and 0 <= nj < n:
                if dist[ni][nj] == -1:
                    dist[ni][nj] = dist[i][j] + 1
                    if grid[ni][nj] == 1 and (ni, nj) not in [(x, y) for x, y in island_cells]:
                        # Reached second island
                        return dist[ni][nj] - 1
                    queue.append((ni, nj))

    return 0


CASES = [
    {
        "grid": [
            [0, 1, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 0],
        ],
    },
    {
        "grid": [
            [1, 1, 1, 1, 1],
            [1, 0, 0, 0, 1],
            [1, 0, 1, 0, 1],
            [1, 0, 0, 0, 1],
            [1, 1, 1, 1, 1],
        ],
    },
    {
        "grid": [
            [1, 0, 0],
            [0, 0, 0],
            [0, 0, 1],
        ],
    },
    {
        "grid": [
            [1, 0],
            [0, 1],
        ],
    },
    {
        "grid": [
            [1, 1, 0, 0, 0],
            [1, 1, 0, 0, 0],
            [0, 0, 0, 1, 1],
            [0, 0, 0, 1, 1],
        ],
    },
    {
        "grid": [[1]],
    },
    {
        "grid": [
            [1, 1, 0, 1, 0],
            [0, 1, 0, 0, 1],
            [1, 0, 0, 0, 0],
            [0, 0, 0, 1, 0],
            [1, 0, 1, 0, 1],
        ],
    },
    {
        "grid": [
            [1, 0, 1],
            [1, 0, 0],
            [0, 0, 1],
        ],
    },
]


if __name__ == '__main__':
    results = []
    for idx, case in enumerate(CASES):
        # Handle stdin path: also accept via stdin if provided
        # But per problem spec we run on CASES
        result = solve(case["grid"])
        results.append({
            "id": idx,
            "input": {"grid": case["grid"]},
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })

    # Also read from stdin if provided (for actual judge)
    data = sys.stdin.read().strip().split()
    if data:
        n = int(data[0])
        grid_in = []
        idx = 1
        for _ in range(n):
            row = list(map(int, data[idx:idx + n]))
            grid_in.append(row)
            idx += n
        stdin_result = solve(grid_in)
        print(json.dumps(stdin_result))
    else:
        print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
