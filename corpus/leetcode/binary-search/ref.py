def solve(arr, target):
    lo, hi = 0, len(arr) - 1
    while lo <= hi:
        mid = lo + (hi - lo) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1


CASES = [
    {"arr": [1, 3, 5, 7, 9], "target": 7},
    {"arr": [1], "target": 1},
    {"arr": [1], "target": 0},
    {"arr": [1], "target": 2},
    {"arr": [1, 2, 3, 4, 5], "target": 3},
    {"arr": [-5, -3, -1, 0, 2, 4], "target": -4},
    {"arr": [-5, -3, -1, 0, 2, 4], "target": 4},
    {"arr": [1, 2, 2, 2, 3, 4], "target": 2},
]


if __name__ == '__main__':
    import json
    out = []
    for i, c in enumerate(CASES):
        result = solve(c["arr"], c["target"])
        out.append({
            "id": i,
            "input": c,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
