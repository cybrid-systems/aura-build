def next_permutation(arr):
    n = len(arr)
    if n <= 1:
        return arr
    i = n - 2
    while i >= 0 and arr[i] >= arr[i + 1]:
        i -= 1
    if i >= 0:
        j = n - 1
        while arr[j] <= arr[i]:
            j -= 1
        arr[i], arr[j] = arr[j], arr[i]
    left = i + 1
    right = n - 1
    while left < right:
        arr[left], arr[right] = arr[right], arr[left]
        left += 1
        right -= 1
    return arr


def solve(n, arr):
    return next_permutation(arr)


CASES = [
    {"n": 3, "arr": [1, 2, 3]},
    {"n": 3, "arr": [3, 2, 1]},
    {"n": 3, "arr": [1, 1, 5]},
    {"n": 4, "arr": [1, 3, 2, 4]},
    {"n": 4, "arr": [1, 2, 3, 4]},
    {"n": 1, "arr": [1]},
    {"n": 4, "arr": [2, 3, 1, 3]},
    {"n": 5, "arr": [5, 4, 3, 2, 1]},
]


if __name__ == '__main__':
    import json
    out = []
    for i, case in enumerate(CASES):
        n = case["n"]
        arr = list(case["arr"])
        result = solve(n, arr)
        out.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
