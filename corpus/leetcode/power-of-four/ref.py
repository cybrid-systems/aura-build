def solve(n):
    return bool(n > 0 and (n & (n - 1)) == 0 and (n & 0x55555555) != 0)


CASES = [
    {"n": 16},
    {"n": 5},
    {"n": 1},
    {"n": -4},
    {"n": 0},
    {"n": 4},
    {"n": 64},
    {"n": 8},
]


if __name__ == '__main__':
    import json
    results = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        output = "true" if result else "false"
        results.append({"id": i, "input": case, "expected": json.dumps(output, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
