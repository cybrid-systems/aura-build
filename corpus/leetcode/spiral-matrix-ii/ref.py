import json
import sys


def solve(n: int) -> list[list[int]]:
    """Construct an n x n spiral matrix with numbers 1..n^2."""
    if n <= 0:
        return []
    matrix = [[0] * n for _ in range(n)]
    top, bottom = 0, n - 1
    left, right = 0, n - 1
    num = 1
    total = n * n
    while num <= total:
        # go right along the top row
        for c in range(left, right + 1):
            matrix[top][c] = num
            num += 1
        top += 1
        if num > total:
            break
        # go down along the right column
        for r in range(top, bottom + 1):
            matrix[r][right] = num
            num += 1
        right -= 1
        if num > total:
            break
        # go left along the bottom row
        for c in range(right, left - 1, -1):
            matrix[bottom][c] = num
            num += 1
        bottom -= 1
        if num > total:
            break
        # go up along the left column
        for r in range(bottom, top - 1, -1):
            matrix[r][left] = num
            num += 1
        left += 1
    return matrix


CASES = [
    {"n": 1},
    {"n": 2},
    {"n": 3},
    {"n": 4},
    {"n": 5},
    {"n": 6},
    {"n": 7},
    {"n": 10},
]


def _canon(obj):
    return json.dumps(obj, separators=(',', ':'), ensure_ascii=False)


if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        n = case["n"]
        out = solve(n)
        results.append({
            "id": i,
            "input": {"n": n},
            "expected": _canon(out),
        })
    sys.stdout.write(_canon(results))
