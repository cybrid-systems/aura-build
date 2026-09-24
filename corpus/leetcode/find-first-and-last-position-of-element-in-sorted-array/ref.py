def solve(a, target):
    n = len(a)
    if n == 0:
        return (-1, -1)
    # Find leftmost position
    lo, hi = 0, n - 1
    left = -1
    while lo <= hi:
        mid = (lo + hi) // 2
        if a[mid] < target:
            lo = mid + 1
        else:
            if a[mid] == target:
                left = mid
            hi = mid - 1
    if left == -1:
        return (-1, -1)
    # Find rightmost position
    lo, hi = 0, n - 1
    right = -1
    while lo <= hi:
        mid = (lo + hi) // 2
        if a[mid] > target:
            hi = mid - 1
        else:
            if a[mid] == target:
                right = mid
            lo = mid + 1
    return (left, right)


CASES = [
    {"a": [5, 7, 7, 8, 8, 10], "target": 8},
    {"a": [5, 7, 7, 8, 8, 10], "target": 6},
    {"a": [1], "target": 1},
    {"a": [], "target": 0},
    {"a": [1, 2, 3, 4, 5], "target": 3},
    {"a": [1, 1, 1, 1, 1], "target": 1},
    {"a": [2, 2], "target": 3},
    {"a": [-5, -3, -1, 0, 2, 4, 6], "target": -1},
]


if __name__ == '__main__':
    import json
    out = []
    for i, c in enumerate(CASES):
        result = solve(c["a"], c["target"])
        out.append({
            "id": i,
            "input": {"a": c["a"], "target": c["target"]},
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
