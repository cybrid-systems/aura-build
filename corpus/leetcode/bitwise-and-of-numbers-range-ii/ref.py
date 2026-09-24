import json

def solve(m, n):
    shift = 0
    while m != n:
        m >>= 1
        n >>= 1
        shift += 1
    return m << shift

CASES = [
    {"m": 5, "n": 7},
    {"m": 0, "n": 0},
    {"m": 1, "n": 1},
    {"m": 0, "n": 2147483647},
    {"m": 2147483647, "n": 2147483647},
    {"m": 1, "n": 2147483647},
    {"m": 12, "n": 15},
    {"m": 600000000, "n": 2147483647},
]

if __name__ == '__main__':
    out = []
    for i, case in enumerate(CASES):
        result = solve(case["m"], case["n"])
        out.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
