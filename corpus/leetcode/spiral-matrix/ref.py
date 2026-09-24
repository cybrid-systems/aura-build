import sys
import json


def spiral_order(matrix):
    if not matrix or not matrix[0]:
        return []
    result = []
    top, bottom = 0, len(matrix) - 1
    left, right = 0, len(matrix[0]) - 1
    while top <= bottom and left <= right:
        for j in range(left, right + 1):
            result.append(matrix[top][j])
        top += 1
        if top > bottom:
            break
        for i in range(top, bottom + 1):
            result.append(matrix[i][right])
        right -= 1
        if left > right:
            break
        for j in range(right, left - 1, -1):
            result.append(matrix[bottom][j])
        bottom -= 1
        if top > bottom:
            break
        for i in range(bottom, top - 1, -1):
            result.append(matrix[i][left])
        left += 1
    return result


def solve(matrix):
    return spiral_order(matrix)


CASES = [
    {"matrix": [[1, 2, 3], [4, 5, 6], [7, 8, 9]]},
    {"matrix": [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]]},
    {"matrix": [[1, 2, 3]]},
    {"matrix": [[1], [2], [3]]},
    {"matrix": [[1]]},
    {"matrix": [[1, 2], [3, 4]]},
    {"matrix": [[1, 2, 3, 4, 5], [6, 7, 8, 9, 10], [11, 12, 13, 14, 15]]},
    {"matrix": [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16]]},
]


if __name__ == '__main__':
    out = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        out.append({"id": i, "input": case, "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
