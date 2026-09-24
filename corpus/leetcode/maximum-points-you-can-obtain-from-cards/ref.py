def solve(card_points: list[int], k: int) -> int:
    n = len(card_points)
    if k == n:
        return sum(card_points)
    total = sum(card_points)
    window_len = n - k
    # initial window sum of length window_len
    cur = sum(card_points[:window_len])
    best = cur
    for i in range(window_len, n):
        cur += card_points[i] - card_points[i - window_len]
        if cur < best:
            best = cur
    return total - best


CASES = [
    {"card_points": [1, 2, 3, 4, 5, 6, 1], "k": 3},
    {"card_points": [2, 2, 2], "k": 2},
    {"card_points": [9, 7, 5, 3, 1], "k": 5},
    {"card_points": [1, 2, 3, 4, 5], "k": 1},
    {"card_points": [1, 2, 3, 4, 5], "k": 4},
    {"card_points": [-1, -2, -3, -4, -5], "k": 2},
    {"card_points": [100, 0, -100, 0, 100], "k": 2},
    {"card_points": [1], "k": 1},
]


if __name__ == '__main__':
    import json
    results = []
    for i, case in enumerate(CASES):
        out = solve(**case)
        results.append({
            "id": i,
            "input": case,
            "expected": json.dumps(out, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
