import sys
import json

def solve(MATRIX, TARGET):
    if not MATRIX or not MATRIX[0]:
        return False
    m = len(MATRIX)
    n = len(MATRIX[0])
    i, j = 0, n - 1
    while i < m and j >= 0:
        val = MATRIX[i][j]
        if val == TARGET:
            return True
        elif val > TARGET:
            j -= 1
        else:
            i += 1
    return False

CASES = [
    {"MATRIX": [[1,4,7,11,15],[2,5,8,12,19],[3,6,9,16,22],[10,13,14,17,24],[18,21,23,26,30]], "TARGET": 5},
    {"MATRIX": [[1,4,7,11,15],[2,5,8,12,19],[3,6,9,16,22],[10,13,14,17,24],[18,21,23,26,30]], "TARGET": 20},
    {"MATRIX": [[1,4,7,11,15],[2,5,8,12,19],[3,6,9,16,22],[10,13,14,17,24],[18,21,23,26,30]], "TARGET": 1},
    {"MATRIX": [[1,4,7,11,15],[2,5,8,12,19],[3,6,9,16,22],[10,13,14,17,24],[18,21,23,26,30]], "TARGET": 30},
    {"MATRIX": [[-5]], "TARGET": -5},
    {"MATRIX": [[-5]], "TARGET": 0},
    {"MATRIX": [[1,2,3],[4,5,6],[7,8,9]], "TARGET": 7},
    {"MATRIX": [], "TARGET": 1},
    {"MATRIX": [[]], "TARGET": 1},
    {"MATRIX": [[1,3,5,7],[2,4,6,8],[10,12,14,16]], "TARGET": 11},
]

if __name__ == '__main__':
    results = []
    for idx, case in enumerate(CASES):
        out = solve(**case)
        results.append({
            "id": idx,
            "input": json.dumps(case, separators=(',', ':'), ensure_ascii=False),
            "expected": json.dumps(out, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
