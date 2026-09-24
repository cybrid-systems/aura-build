def solve(arr):
    n = len(arr)
    i = 0
    while i < n:
        v = arr[i]
        # Place value v at index v-1 if 1 <= v <= n and not already there.
        if 1 <= v <= n and arr[v - 1] != v:
            # Swap arr[i] and arr[v-1]
            arr[i], arr[v - 1] = arr[v - 1], arr[i]
        else:
            i += 1
    # Scan for the first index where arr[i] != i+1
    for i in range(n):
        if arr[i] != i + 1:
            return i + 1
    return n + 1


CASES = [
    {"id": 0, "input": [3, 4, -1, 1]},
    {"id": 1, "input": [1, 2, 0]},
    {"id": 2, "input": [-5, -1, 0]},
    {"id": 3, "input": [1, 2, 3, 4]},
    {"id": 4, "input": [2, 2, 2, 2]},
    {"id": 5, "input": [7, 8, 9, 11, 12]},
    {"id": 6, "input": [1]},
    {"id": 7, "input": [2]},
]


if __name__ == '__main__':
    import json
    out = []
    for case in CASES:
        arr = list(case["input"])  # copy to allow in-place modification
        result = solve(arr)
        out.append({
            "id": case["id"],
            "input": case["input"],
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
