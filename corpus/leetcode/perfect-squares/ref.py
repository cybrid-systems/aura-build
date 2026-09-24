def solve(n: int) -> int:
    if n <= 0:
        return 0
    # Lagrange's four-square theorem: answer is 1, 2, 3, or 4 for n > 0
    # Check if n is a perfect square -> 1
    if int(n ** 0.5) ** 2 == n:
        return 1
    # Check if n can be expressed as sum of two squares
    i = 1
    while i * i <= n:
        j_sq = n - i * i
        if int(j_sq ** 0.5) ** 2 == j_sq:
            return 2
        i += 1
    # Check Legendre's three-square theorem: n not of form 4^a(8b+7)
    m = n
    while m % 4 == 0:
        m //= 4
    if m % 8 != 7:
        return 3
    return 4


CASES = [
    {"n": 0},
    {"n": 1},
    {"n": 2},
    {"n": 3},
    {"n": 4},
    {"n": 7},
    {"n": 12},
    {"n": 13},
    {"n": 100},
    {"n": 9999},
]


if __name__ == '__main__':
    import json
    results = []
    for i, case in enumerate(CASES):
        out = solve(**case)
        results.append({"id": i, "input": case, "expected": json.dumps(out, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
