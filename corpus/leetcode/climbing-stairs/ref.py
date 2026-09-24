import sys
import json

def solve(n):
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a

CASES = [
    {"n": 1},
    {"n": 2},
    {"n": 3},
    {"n": 4},
    {"n": 5},
    {"n": 10},
    {"n": 44},
    {"n": 45},
]

if __name__ == '__main__':
    out = []
    for i, case in enumerate(CASES):
        result = solve(case["n"])
        out.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
