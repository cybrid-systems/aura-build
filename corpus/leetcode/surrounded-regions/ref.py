from collections import deque


def solve(board: list[str]) -> list[str]:
    if not board or not board[0]:
        return board
    m, n = len(board), len(board[0])
    if m == 1 or n == 1:
        return board

    grid = [list(row) for row in board]
    q = deque()

    for i in range(m):
        if grid[i][0] == 'O':
            grid[i][0] = 'S'
            q.append((i, 0))
        if grid[i][n - 1] == 'O':
            grid[i][n - 1] = 'S'
            q.append((i, n - 1))

    for j in range(n):
        if grid[0][j] == 'O':
            grid[0][j] = 'S'
            q.append((0, j))
        if grid[m - 1][j] == 'O':
            grid[m - 1][j] = 'S'
            q.append((m - 1, j))

    while q:
        r, c = q.popleft()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < m and 0 <= nc < n and grid[nr][nc] == 'O':
                grid[nr][nc] = 'S'
                q.append((nr, nc))

    for i in range(m):
        for j in range(n):
            if grid[i][j] == 'O':
                grid[i][j] = 'X'
            elif grid[i][j] == 'S':
                grid[i][j] = 'O'

    return [''.join(row) for row in grid]


CASES = [
    {"board": ["XXXX", "XOOX", "XXOX", "XOXX"]},
    {"board": ["OOXX", "OOOO", "XXOO", "OOOO"]},
    {"board": ["X"]},
    {"board": ["OOOO"]},
    {"board": ["XXXXX", "XOOOX", "XOXOX", "XOOOX", "XXXXX"]},
    {"board": ["XOO", "OOO", "XOX"]},
    {"board": []},
    {"board": ["OXOX", "XOXO", "OXOX", "XOXO"]},
]


if __name__ == '__main__':
    import json
    out = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        if isinstance(result, list) and result and isinstance(result[0], list):
            result = [''.join(row) for row in result]
        out.append({"id": i, "input": case, "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
