import os
import json


def solve(m, n, grid):
    result = []
    total = m + n - 2
    for s in range(total + 1):
        i = max(0, s - n + 1)
        j = min(s, n - 1)
        diag = []
        while i < m and j >= 0:
            diag.append(grid[i][j])
            i += 1
            j -= 1
        if s % 2 == 0:
            diag.reverse()
        result.extend(diag)
    return result


def parse_case(case_str):
    lines = case_str.strip().split("\n")
    parts = lines[0].split()
    m = int(parts[0])
    n = int(parts[1])
    grid = []
    for i in range(m):
        row = list(map(int, lines[1 + i].split()))
        grid.append(row)
    return {"m": m, "n": n, "grid": grid}


def main():
    cases = []
    # Case 0: Example 1 - 3x3
    cases.append({"m": 3, "n": 3, "grid": [[1, 2, 3], [4, 5, 6], [7, 8, 9]]})
    # Case 1: Example 2 - 2x2
    cases.append({"m": 2, "n": 2, "grid": [[1, 2], [3, 4]]})
    # Case 2: 1x1
    cases.append({"m": 1, "n": 1, "grid": [[42]]})
    # Case 3: 1x4 single row
    cases.append({"m": 1, "n": 4, "grid": [[1, 2, 3, 4]]})
    # Case 4: 4x1 single column
    cases.append({"m": 4, "n": 1, "grid": [[1], [2], [3], [4]]})
    # Case 5: 2x3
    cases.append({"m": 2, "n": 3, "grid": [[1, 2, 3], [4, 5, 6]]})
    # Case 6: 3x2
    cases.append({"m": 3, "n": 2, "grid": [[1, 2], [3, 4], [5, 6]]})
    # Case 7: 5x5 with negatives
    cases.append({"m": 5, "n": 5, "grid": [
        [-1, -2, -3, -4, -5],
        [-6, -7, -8, -9, -10],
        [-11, -12, -13, -14, -15],
        [-16, -17, -18, -19, -20],
        [-21, -22, -23, -24, -25]
    ]})

    output = []
    for idx, c in enumerate(cases):
        res = solve(c["m"], c["n"], c["grid"])
        output.append({
            "id": idx,
            "input": c,
            "expected": json.dumps(res, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(output, separators=(',', ':'), ensure_ascii=False))


if __name__ == '__main__':
    main()
