def solve(n: int) -> bool:
    if n <= 0:
        return False
    while n % 3 == 0:
        n //= 3
    return n == 1


CASES = [
    {"n": 27},
    {"n": 0},
    {"n": 45},
    {"n": 1},
    {"n": 3},
    {"n": 9},
    {"n": -3},
    {"n": 1162261467},
    {"n": 1162261466},
    {"n": 3**20},
]


if __name__ == '__main__':
    import json
    results = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        results.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
