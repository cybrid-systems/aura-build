from collections import deque
import json

def solve(H, W, grid):
    if H == 0 or W == 0:
        return 0
    grid = [list(row) for row in grid]
    count = 0
    for i in range(H):
        for j in range(W):
            if grid[i][j] == '1':
                count += 1
                grid[i][j] = '0'
                queue = deque([(i, j)])
                while queue:
                    r, c = queue.popleft()
                    for dr, dc in ((-1,0),(1,0),(0,-1),(0,1)):
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < H and 0 <= nc < W and grid[nr][nc] == '1':
                            grid[nr][nc] = '0'
                            queue.append((nr, nc))
    return count

CASES = [
    {"H": 4, "W": 5, "grid": ["11110", "11010", "11000", "00000"]},
    {"H": 4, "W": 5, "grid": ["11000", "11000", "00100", "00011"]},
    {"H": 1, "W": 1, "grid": ["1"]},
    {"H": 1, "W": 1, "grid": ["0"]},
    {"H": 1, "W": 4, "grid": ["1111"]},
    {"H": 3, "W": 3, "grid": ["101", "010", "101"]},
    {"H": 4, "W": 4, "grid": ["1100", "1110", "0110", "0001"]},
    {"H": 3, "W": 3, "grid": ["000", "000", "000"]},
]

if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        result = solve(case["H"], case["W"], case["grid"])
        results.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
