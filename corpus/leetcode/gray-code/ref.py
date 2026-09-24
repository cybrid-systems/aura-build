def solve(n: int) -> list[int]:
    if n <= 0:
        return []
    result = [0]
    for i in range(n):
        size = 1 << i
        for j in range(size - 1, -1, -1):
            result.append(result[j] | (1 << i))
    return result


CASES = [
    {"n": 1},
    {"n": 2},
    {"n": 3},
    {"n": 4},
    {"n": 5},
    {"n": 8},
    {"n": 16},
    {"n": 0},
]


if __name__ == '__main__':
    import json
    out = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        out.append({"id": i, "input": case, "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
