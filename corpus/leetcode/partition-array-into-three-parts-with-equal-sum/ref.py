import json
import sys

def solve(arr):
    n = len(arr)
    if n < 3:
        return "NO"
    total = sum(arr)
    if total % 3 != 0:
        return "NO"
    target = total // 3
    count = 0
    current = 0
    if target == 0:
        # Need to find 2 zero-sum split points before the last element
        zero_count = 0
        cur = 0
        for idx in range(n - 1):
            cur += arr[idx]
            if cur == 0:
                zero_count += 1
                if zero_count == 2:
                    return "YES"
        return "NO"
    else:
        for idx in range(n - 1):
            current += arr[idx]
            if current == target:
                count += 1
                current = 0
                if count == 2:
                    return "YES"
        return "NO"

CASES = [
    {"arr": [0, 2, 1, -6, 6, -7, 9, 1, 2, 0, 1]},
    {"arr": [1, -1, 1, -1, 1, -1, 1, -1]},
    {"arr": [1, 2, 3, 4, 5]},
    {"arr": [0, 0, 0, 0]},
    {"arr": [1, 2, 3]},
    {"arr": [-1, -1, -1, -1, -1, -1]},
    {"arr": [3, 3, 3, 3]},
    {"arr": [5, 5, 5, 5, 5]},
]

if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        result = solve(case["arr"])
        results.append({"id": i, "input": case, "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
