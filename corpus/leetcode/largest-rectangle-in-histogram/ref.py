from __future__ import annotations
import json

def solve(heights: list[int]) -> int:
    if not heights:
        return 0
    stack: list[int] = []
    max_area = 0
    extended = heights + [0]
    for i, h in enumerate(extended):
        while stack and extended[stack[-1]] > h:
            top = stack.pop()
            height = extended[top]
            if stack:
                width = i - stack[-1] - 1
            else:
                width = i
            area = height * width
            if area > max_area:
                max_area = area
        stack.append(i)
    return max_area


CASES = [
    {"heights": [2, 1, 5, 6, 2, 3]},
    {"heights": [2, 4]},
    {"heights": [0, 0]},
    {"heights": [1]},
    {"heights": [1, 1, 1, 1]},
    {"heights": [4, 2, 0, 3, 2, 5]},
    {"heights": [0]},
    {"heights": [6, 7, 5, 2, 4, 5, 9, 3]},
]


if __name__ == "__main__":
    results = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        results.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
