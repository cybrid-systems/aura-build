def solve(arr):
    n = len(arr)
    if n < 3:
        return 0
    longest = 0
    i = 1
    while i < n - 1:
        # Check if arr[i] is a peak
        if arr[i] > arr[i - 1] and arr[i] > arr[i + 1]:
            # Walk left to find the start of the mountain
            left = i - 1
            while left > 0 and arr[left - 1] < arr[left]:
                left -= 1
            # Walk right to find the end of the mountain
            right = i + 1
            while right < n - 1 and arr[right] > arr[right + 1]:
                right += 1
            longest = max(longest, right - left + 1)
            i = right + 1
        else:
            i += 1
    return longest


CASES = [
    {"arr": [2, 1, 4, 7, 3, 2, 5]},
    {"arr": [2, 2, 2]},
    {"arr": [1, 3, 1, 4, 5, 6, 7, 8, 9, 8, 7, 6, 5, 4, 3, 2, 0]},
    {"arr": [1, 2, 3]},
    {"arr": [3, 2, 1]},
    {"arr": [1]},
    {"arr": [1, 2, 3, 4, 5, 6, 7, 8, 9]},
    {"arr": [9, 8, 7, 6, 5, 4, 3, 2, 1]},
    {"arr": [1, 2, 3, 2, 1, 2, 3, 2, 1]},
    {"arr": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0]},
]


if __name__ == "__main__":
    import json
    out = []
    for i, case in enumerate(CASES):
        result = solve(case["arr"])
        out.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
