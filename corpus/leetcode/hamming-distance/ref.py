import sys
import json

def solve(x, y):
    xor = x ^ y
    count = 0
    while xor:
        count += xor & 1
        xor >>= 1
    return count

CASES = [
    {"x": 1, "y": 4},
    {"x": 3, "y": 1},
    {"x": 0, "y": 0},
    {"x": 7, "y": 8},
    {"x": 0, "y": 4294967295},
    {"x": 4294967295, "y": 4294967295},
    {"x": 123456789, "y": 987654321},
    {"x": 1, "y": 1},
]

if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        result = solve(case["x"], case["y"])
        results.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
