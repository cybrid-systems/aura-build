def solve(arr):
    lo, hi = 0, len(arr) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if arr[mid] < arr[mid + 1]:
            lo = mid + 1
        else:
            hi = mid
    return lo


CASES = [
    {"arr": [0, 1, 2, 4, 7, 5, 3, 1]},
    {"arr": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 8, 7, 6, 5, 4, 3, 2, 1]},
    {"arr": [0, 1, 2, 3, 4, 5] + [5] + [5, 4, 3, 2, 1, 0]},  # construct via concatenation below
    {"arr": [1, 3, 5, 7, 6, 4, 2]},
    {"arr": [0, 2, 4, 6, 8, 10, 12, 11]},
    {"arr": [1, 2, 3, 4, 5, 4, 3, 2, 1]},
    {"arr": [5, 10, 15, 20, 25, 20]},
    {"arr": [1, 2, 3, 4, 5, 6, 7, 8, 7, 6, 5, 4, 3, 2, 1]},
]

# fix the constructed case properly
CASES[2]["arr"] = list(range(0, 11)) + list(range(9, -1, -1))


if __name__ == '__main__':
    import json
    out = []
    for i, c in enumerate(CASES):
        res = solve(c["arr"])
        out.append({"id": i, "input": {"arr": c["arr"]}, "expected": json.dumps(res, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
