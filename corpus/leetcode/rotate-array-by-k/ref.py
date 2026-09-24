import json

def solve(arr, k):
    n = len(arr)
    if n == 0:
        return arr
    k = k % n
    if k == 0:
        return arr
    # Three reversals for in-place right rotation by k
    def reverse(a, lo, hi):
        # reverse the subarray a[lo:hi+1] in-place
        i, j = lo, hi
        while i < j:
            a[i], a[j] = a[j], a[i]
            i += 1
            j -= 1
    reverse(arr, 0, n - 1)
    reverse(arr, 0, k - 1)
    reverse(arr, k, n - 1)
    return arr

CASES = [
    {"arr": [1, 2, 3, 4, 5, 6, 7], "k": 3},
    {"arr": [1, 2, 3, 4, 5], "k": 0},
    {"arr": [1, 2, 3, 4, 5], "k": 5},
    {"arr": [1, 2, 3, 4, 5], "k": 7},
    {"arr": [], "k": 3},
    {"arr": [42], "k": 100},
    {"arr": [-1, -2, -3, -4], "k": 1},
    {"arr": [1, 2, 3, 4, 5, 6], "k": 2},
]

if __name__ == '__main__':
    out = []
    for i, c in enumerate(CASES):
        result = solve(c["arr"][:], c["k"])
        expected = json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        out.append({
            "id": i,
            "input": {"arr": c["arr"], "k": c["k"]},
            "expected": expected
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
