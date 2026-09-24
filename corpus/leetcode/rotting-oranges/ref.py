def solve(grid):
    from collections import deque
    if not grid or not grid[0]:
        return 0
    rows = len(grid)
    cols = len(grid[0])
    queue = deque()
    fresh = 0
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == 2:
                queue.append((r, c, 0))
            elif grid[r][c] == 1:
                fresh += 1
    if fresh == 0:
        return 0
    minutes = 0
    while queue:
        r, c, t = queue.popleft()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 1:
                grid[nr][nc] = 2
                fresh -= 1
                queue.append((nr, nc, t + 1))
                minutes = t + 1
    return minutes if fresh == 0 else -1


CASES = [
    {"grid": [[2, 1, 1], [1, 1, 0], [0, 1, 1]]},
    {"grid": [[2, 1, 1], [0, 1, 0], [1, 1, 1]]},
    {"grid": [[0, 2]]},
    {"grid": [[1]]},
    {"grid": []},
    {"grid": [[0]]},
    {"grid": [[1, 2, 1, 1]]},
    {"grid": [[2, 2], [1, 1], [1, 1]]},
]


if __name__ == '__main__':
    import json, copy
    results = []
    for i, case in enumerate(CASES):
        grid_copy = copy.deepcopy(case['grid'])
        res = solve(grid_copy)
        results.append({
            "id": i,
            "input": case,
            "expected": json.dumps(res, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
