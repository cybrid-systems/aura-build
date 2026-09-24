def solve(n):
    if n < 0:
        return []
    bits = [0] * (n + 1)
    for i in range(1, n + 1):
        bits[i] = bits[i >> 1] + (i & 1)
    return bits


CASES = [
    {"n": 2},
    {"n": 5},
    {"n": 0},
    {"n": 1},
    {"n": 7},
    {"n": 10},
    {"n": 16},
    {"n": 100},
]


if __name__ == '__main__':
    import json
    results = []
    for i, case in enumerate(CASES):
        out = solve(**case)
        results.append({
            "id": i,
            "input": case,
            "expected": json.dumps(out, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
