import json
import sys

def solve(n, k, x, arr):
    lo, hi = 0, n - k
    while lo < hi:
        mid = (lo + hi) // 2
        # Compare window starting at mid vs mid+1
        # window [mid] wins if x - arr[mid] <= arr[mid+k] - x
        if x - arr[mid] <= arr[mid + k] - x:
            hi = mid
        else:
            lo = mid + 1
    return arr[lo:lo + k]


CASES = [
    {"n": 7, "k": 3, "x": 5, "arr": [1, 2, 3, 4, 7, 8, 9]},
    {"n": 7, "k": 4, "x": 5, "arr": [1, 2, 3, 4, 7, 8, 9]},
    {"n": 5, "k": 5, "x": 3, "arr": [1, 2, 3, 4, 5]},
    {"n": 4, "k": 1, "x": 10, "arr": [1, 2, 3, 100]},
    {"n": 4, "k": 1, "x": -5, "arr": [-10, -3, 0, 5]},
    {"n": 6, "k": 3, "x": 0, "arr": [-5, -2, -1, 1, 2, 3]},
    {"n": 8, "k": 4, "x": 4, "arr": [1, 2, 3, 4, 5, 6, 7, 8]},
    {"n": 5, "k": 2, "x": 100, "arr": [1, 50, 80, 120, 150]},
]


if __name__ == '__main__':
    out = []
    for idx, case in enumerate(CASES):
        n = case["n"]
        k = case["k"]
        x = case["x"]
        arr = case["arr"]
        result = solve(n, k, x, arr)
        out.append({
            "id": idx,
            "input": {
                "n": n,
                "k": k,
                "x": x,
                "arr": arr,
            },
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })
    sys.stdout.write(json.dumps(out, separators=(',', ':'), ensure_ascii=False) + "\n")
