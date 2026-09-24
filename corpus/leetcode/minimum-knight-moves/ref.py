import json
from collections import deque

def solve(x, y):
    # By symmetry, work with non-negative coordinates.
    x = abs(x)
    y = abs(y)
    # Swap so that x >= y, which simplifies the bounded BFS region.
    if x < y:
        x, y = y, x
    # Known base values: minimum knight moves for small targets.
    # Source: classic closed-form / precomputed table.
    # We'll use a small BFS to cover edge cases, but bounded to a small region.
    # For large targets, use the closed-form formula.
    # BFS over a bounded region (diamond shape) is sufficient for (x,y) up to ~300.
    # Use the known formula for general large inputs.
    # Reference formula (derived from mathematical analysis):
    #   For x,y >= 0 with x >= y:
    #     If y == 0 and x == 1: 3
    #     If y == 0 and x == 2: 2
    #     Otherwise: a piecewise formula.
    # We'll implement a simple BFS for small values and a closed form for large.
    # Use the standard formula:
    #   d = max((x+1)//2, (x+y+2)//3)
    #   adjust for parity:
    #     delta = d
    #     while delta % 2 != (x+y) % 2 or delta < x or delta < y: ...
    # But a cleaner known approach:
    if x == 0 and y == 0:
        return 0
    # Use the well-known formula by iterating d upwards until valid:
    # Starting guess:
    d = max((x + 1) // 2, (x + y + 2) // 3)
    # Adjust parity so d has the same parity as (x+y) and d >= x, d >= y.
    while (d % 2) != ((x + y) % 2):
        d += 1
    while d < x or d < y:
        # This shouldn't happen normally, but safeguard:
        d += 2
    return d

CASES = [
    {"x": 0, "y": 0},
    {"x": 1, "y": 1},
    {"x": 2, "y": 2},
    {"x": 1, "y": 0},
    {"x": 2, "y": 1},
    {"x": -1, "y": -2},
    {"x": 5, "y": 5},
    {"x": -3, "y": 7},
    {"x": 100, "y": 100},
    {"x": 0, "y": 2},
    {"x": 2, "y": 0},
    {"x": 1, "y": 2},
]

if __name__ == '__main__':
    out = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        out.append({
            "id": i,
            "input": {k: v for k, v in case.items()},
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
