from collections import deque
import json

def solve(screen: list[list[int]], sr: int, sc: int, new_color: int) -> list[list[int]]:
    if not screen or not screen[0]:
        return screen
    
    m, n = len(screen), len(screen[0])
    original_color = screen[sr][sc]
    
    if original_color == new_color:
        return screen
    
    # BFS approach
    queue = deque([(sr, sc)])
    while queue:
        r, c = queue.popleft()
        if (r < 0 or r >= m or c < 0 or c >= n
            or screen[r][c] != original_color):
            continue
        screen[r][c] = new_color
        queue.append((r + 1, c))
        queue.append((r - 1, c))
        queue.append((r, c + 1))
        queue.append((r, c - 1))
    
    return screen


CASES = [
    {
        "screen": [[1, 1, 1], [1, 1, 0], [1, 0, 1]],
        "sr": 1,
        "sc": 1,
        "new_color": 2,
    },
    {
        "screen": [[0, 0, 0], [0, 0, 0]],
        "sr": 0,
        "sc": 0,
        "new_color": 0,
    },
    {
        "screen": [[0, 0, 0], [0, 0, 0]],
        "sr": 0,
        "sc": 1,
        "new_color": 1,
    },
    {
        "screen": [[5]],
        "sr": 0,
        "sc": 0,
        "new_color": 9,
    },
    {
        "screen": [[1, 2, 1], [2, 1, 2], [1, 2, 1]],
        "sr": 0,
        "sc": 0,
        "new_color": 3,
    },
    {
        "screen": [
            [1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1],
        ],
        "sr": 1,
        "sc": 2,
        "new_color": 7,
    },
    {
        "screen": [
            [0, 1, 0],
            [1, 1, 1],
            [0, 1, 0],
        ],
        "sr": 1,
        "sc": 1,
        "new_color": 5,
    },
    {
        "screen": [[1, 0], [0, 1]],
        "sr": 0,
        "sc": 0,
        "new_color": 8,
    },
]


if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        # Make a deep copy of screen so each case is independent
        screen_copy = [row[:] for row in case["screen"]]
        result = solve(
            screen_copy,
            case["sr"],
            case["sc"],
            case["new_color"],
        )
        results.append({
            "id": i,
            "input": {
                "screen": case["screen"],
                "sr": case["sr"],
                "sc": case["sc"],
                "new_color": case["new_color"],
            },
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
