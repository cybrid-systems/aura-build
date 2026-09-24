def solve(n):
    result = 0
    for i in range(32):
        result = (result << 1) | ((n >> i) & 1)
    return result

CASES = [
    {"n": 123456},
    {"n": 0},
    {"n": 4294967295},
    {"n": 1},
    {"n": 1431655765},
    {"n": 2},
    {"n": 2147483648},
    {"n": 2863311530},
]

if __name__ == '__main__':
    import json
    out = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        expected = result
        out.append({"id": i, "input": case, "expected": json.dumps(expected, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
