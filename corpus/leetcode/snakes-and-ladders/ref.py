def solve(n, board_flat):
    n2 = n * n
    # Convert board to 1-indexed squares following boustrophedon numbering.
    # Square 1 is at bottom-left.
    # Row 0 is the bottom row; row n-1 is the top row.
    # Row index increases from bottom to top.
    # In row i (0-indexed from bottom), cells are numbered left-to-right if i is even,
    # right-to-left if i is odd.
    # The input gives rows from row 0 (top) to row n-1 (bottom) as per the problem
    # ("row 0 of board", "row 1 of board", ...). So input row 0 = top row = board row n-1 (bottom-up).
    
    # Let's build mapping: square number -> destination (or itself).
    square_dest = [0] * (n2 + 1)  # 1-indexed
    for i in range(n):
        row_input_idx = i  # 0..n-1, where 0 is the top row in input
        for j in range(n):
            val = board_flat[row_input_idx][j]
            # square number for (row_input_idx, j):
            # The bottom row has input index n-1.
            # board row from bottom = (n - 1) - row_input_idx
            board_row_from_bottom = (n - 1) - row_input_idx
            if board_row_from_bottom % 2 == 0:
                # left-to-right
                square_num = board_row_from_bottom * n + j + 1
            else:
                # right-to-left
                square_num = board_row_from_bottom * n + (n - 1 - j) + 1
            if val == -1:
                square_dest[square_num] = square_num
            else:
                square_dest[square_num] = val
    # Some squares might not be in board if board_flat has missing rows? Assume n rows provided.
    
    # BFS
    from collections import deque
    dist = [-1] * (n2 + 1)
    dist[1] = 0
    q = deque([1])
    while q:
        u = q.popleft()
        d = dist[u]
        if u == n2:
            return d
        for k in range(1, 7):
            v = u + k
            if v > n2:
                continue
            w = square_dest[v]
            if dist[w] == -1:
                dist[w] = d + 1
                q.append(w)
    return -1


def solve_from_input(data):
    lines = data.strip().split('\n')
    n = int(lines[0].split('=')[1])
    board = []
    for i in range(n):
        row = list(map(int, lines[1 + i].split()))
        board.append(row)
    return solve(n, board)


CASES = [
    {"n": 4, "board": [
        [-1, -1, -1, -1],
        [-1, -1, -1, -1],
        [-1, -1, -1, -1],
        [-1, 14, -1, -1],
    ]},
    {"n": 3, "board": [
        [-1, -1, -1],
        [-1, 9, -1],
        [-1, -1, -1],
    ]},
    {"n": 6, "board": [
        [-1, -1, -1, -1, -1, -1],
        [-1, -1, -1, -1, -1, -1],
        [-1, -1, -1, -1, -1, -1],
        [-1, -1, -1, -1, -1, -1],
        [-1, -1, -1, -1, -1, -1],
        [-1, -1, -1, -1, -1, -1],
    ]},
    {"n": 2, "board": [
        [-1, 3],
        [-1, -1],
    ]},
    {"n": 2, "board": [
        [2, -1],
        [-1, -1],
    ]},
    {"n": 5, "board": [
        [-1, -1, -1, -1, -1],
        [-1, -1, -1, -1, -1],
        [-1, -1, -1, -1, -1],
        [-1, -1, -1, -1, -1],
        [-1, -1, -1, -1, -1],
    ]},
    {"n": 3, "board": [
        [-1, -1, 2],
        [-1, -1, -1],
        [-1, -1, -1],
    ]},
    {"n": 3, "board": [
        [-1, -1, 9],
        [-1, -1, -1],
        [-1, -1, -1],
    ]},
]


if __name__ == '__main__':
    import json
    results = []
    for idx, case in enumerate(CASES):
        n = case["n"]
        board = case["board"]
        res = solve(n, board)
        results.append({
            "id": idx,
            "input": {"n": n, "board": board},
            "expected": json.dumps(res, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
