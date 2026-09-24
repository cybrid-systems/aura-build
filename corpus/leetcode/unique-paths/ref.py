import sys
import json

def solve(m, n):
    # Combinatorial formula: C(m+n-2, m-1)
    # Compute using iterative multiplication to avoid overflow issues with intermediate values
    # and to keep it simple.
    total_steps = m + n - 2
    k = min(m - 1, n - 1)
    # C(total_steps, k)
    result = 1
    for i in range(1, k + 1):
        result = result * (total_steps - k + i) // i
    return result

CASES = [
    {"m": 3, "n": 7},
    {"m": 1, "n": 1},
    {"m": 1, "n": 5},
    {"m": 5, "n": 1},
    {"m": 2, "n": 2},
    {"m": 3, "n": 3},
    {"m": 4, "n": 5},
    {"m": 7, "n": 3},
]

if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        out = solve(case["m"], case["n"])
        results.append({
            "id": i,
            "input": case,
            "expected": json.dumps(out, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
