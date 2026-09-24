import json
import sys

def solve(grid):
    """
    Count negative numbers in a matrix where each row and column is sorted
    in non-increasing order.
    Uses O(m + n) walk starting from the top-right corner.
    """
    if not grid or not grid[0]:
        return 0
    m, n = len(grid), len(grid[0])
    count = 0
    r, c = 0, n - 1
    while r < m and c >= 0:
        if grid[r][c] < 0:
            # All values in this row from column 0 to c are negative
            count += c + 1
            r += 1
        else:
            # Move left to find negatives
            c -= 1
    return count


CASES = [
    {"id": 0, "input": {"grid": [
        [4, 3, 2, -1],
        [3, 2, 1, -1],
        [1, 1, -1, -2],
        [-1, -1, -2, -3],
        [-2, -3, -3, -4],
    ]}},
    {"id": 1, "input": {"grid": [
        [3, 2],
        [1, 0],
    ]}},
    {"id": 2, "input": {"grid": [
        [0, 0, 0],
        [0, 0, 0],
    ]}},
    {"id": 3, "input": {"grid": [
        [-1, -1, -1],
        [-1, -1, -1],
    ]}},
    {"id": 4, "input": {"grid": [
        [5, 1, 0],
        [3, -2, -3],
        [1, -5, -7],
    ]}},
    {"id": 5, "input": {"grid": [[1]]}},
    {"id": 6, "input": {"grid": [[-1]]}},
    {"id": 7, "input": {"grid": [
        [0, -1, -2, -3],
        [0, 0, -1, -2],
        [1, 0, 0, -1],
    ]}},
]


if __name__ == '__main__':
    results = []
    for case in CASES:
        inp = case["input"]
        out = solve(**inp)
        results.append({
            "id": case["id"],
            "input": inp,
            "expected": json.dumps(out, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
