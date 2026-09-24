def solve(A: list[int], K: int) -> int:
    n = len(A)
    if n < 2:
        return 0
    left, right = 0, n - 1
    count = 0
    while left < right:
        s = A[left] + A[right]
        if s < K:
            count += right - left
            left += 1
        else:
            right -= 1
    return count


CASES = [
    {"A": [1, 2, 3, 4, 5], "K": 7},
    {"A": [-3, -1, 0, 2, 4], "K": 2},
    {"A": [1, 1, 1, 1], "K": 3},
    {"A": [], "K": 10},
    {"A": [5], "K": 10},
    {"A": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], "K": 1},
    {"A": [-10, -5, -1, 0, 3, 7], "K": 0},
    {"A": [0, 0, 0, 0, 0], "K": 1},
]


if __name__ == '__main__':
    import json
    out = []
    for i, case in enumerate(CASES):
        result = solve(case["A"], case["K"])
        out.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
