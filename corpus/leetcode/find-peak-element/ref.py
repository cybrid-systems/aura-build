def solve(arr):
    n = len(arr)
    lo, hi = 0, n - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if arr[mid] > arr[mid + 1]:
            hi = mid
        else:
            lo = mid + 1
    return lo


CASES = [
    {"arr": [1, 2, 3, 1]},
    {"arr": [1, 2, 1, 3, 5, 6, 4]},
    {"arr": [1]},
    {"arr": [2, 1]},
    {"arr": [1, 2]},
    {"arr": [1, 1, 1, 1, 1]},
    {"arr": [5, 4, 3, 2, 1]},
    {"arr": [1, 2, 3, 4, 6, 5]},
    {"arr": [3, 4, 3, 2, 1]},
    {"arr": [10, 20, 15, 2, 23, 90, 67]},
]


if __name__ == '__main__':
    import json
    results = []
    for i, c in enumerate(CASES):
        arr = c["arr"]
        out = solve(arr)
        results.append({
            "id": i,
            "input": {"arr": arr},
            "expected": json.dumps(out, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
