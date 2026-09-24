import json

def solve(points):
    if not points:
        return 0
    points = sorted(points, key=lambda p: p[1])
    arrows = 1
    arrow_pos = points[0][1]
    for x_start, x_end in points[1:]:
        if x_start > arrow_pos:
            arrows += 1
            arrow_pos = x_end
    return arrows

CASES = [
    {"points": [[10, 16], [2, 8], [1, 6], [7, 12]]},
    {"points": [[1, 2], [3, 4], [5, 6], [7, 8]]},
    {"points": [[1, 2], [2, 3], [3, 4], [4, 5]]},
    {"points": [[0, 1]]},
    {"points": [[1, 10], [2, 5], [6, 9], [3, 8]]},
    {"points": [[-5, 5], [-3, 3], [-1, 1], [0, 2], [4, 8]]},
    {"points": [[1, 2], [2, 3], [2, 4], [5, 6]]},
    {"points": [[1, 3], [2, 4], [3, 5], [4, 6]]},
]

if __name__ == '__main__':
    out = []
    for i, case in enumerate(CASES):
        result = solve([tuple(p) for p in case["points"]])
        out.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
