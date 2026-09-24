import sys
import json

def solve(n):
    return n > 0 and (n & (n - 1)) == 0

CASES = [
    {"n": 1},
    {"n": 16},
    {"n": 3},
    {"n": -4},
    {"n": 1024},
    {"n": 2},
    {"n": -1},
    {"n": 0 + 1},
]

if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        out = "true" if result else "false"
        results.append({
            "id": i,
            "input": case,
            "expected": out
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
