def solve(weights: list[int], D: int) -> int:
    def can_ship(cap: int) -> bool:
        days_needed = 1
        cur = 0
        for w in weights:
            if cur + w <= cap:
                cur += w
            else:
                days_needed += 1
                cur = w
                if days_needed > D:
                    return False
        return True

    lo, hi = max(weights), sum(weights)
    while lo < hi:
        mid = (lo + hi) // 2
        if can_ship(mid):
            hi = mid
        else:
            lo = mid + 1
    return lo


CASES = [
    {"weights": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], "D": 5},
    {"weights": [3, 2, 2, 4, 1, 4], "D": 3},
    {"weights": [1, 2, 3, 1, 1], "D": 4},
    {"weights": [10], "D": 1},
    {"weights": [1, 1, 1, 1], "D": 4},
    {"weights": [1, 1, 1, 1], "D": 1},
    {"weights": [5, 5, 5, 5, 5], "D": 2},
    {"weights": [9, 8, 10, 7, 6, 5], "D": 3},
]


if __name__ == '__main__':
    import json
    out = []
    for i, c in enumerate(CASES):
        result = solve(c["weights"], c["D"])
        out.append({"id": i, "input": c, "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
