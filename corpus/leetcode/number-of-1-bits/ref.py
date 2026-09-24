def solve(n):
    """Count the number of 1 bits in an unsigned 32-bit integer."""
    count = 0
    while n:
        n &= (n - 1)
        count += 1
    return count


CASES = [
    {"n": 0},
    {"n": 1},
    {"n": 11},
    {"n": 128},
    {"n": 255},
    {"n": 4294967295},
    {"n": 4294967293},
    {"n": 2147483648},
]


if __name__ == '__main__':
    import json
    results = []
    for i, case in enumerate(CASES):
        inp = {"n": case["n"]}
        expected = solve(case["n"])
        results.append({
            "id": i,
            "input": inp,
            "expected": json.dumps(expected, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
