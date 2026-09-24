import sys
import json

def solve(n: int) -> int:
    count = 0
    p = 5
    while p <= n:
        count += n // p
        p *= 5
    return count

CASES = [
    {"n": 0},
    {"n": 5},
    {"n": 100},
    {"n": 1},
    {"n": 4},
    {"n": 6},
    {"n": 25},
    {"n": 1000000000},
]

if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        result = solve(case["n"])
        results.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
