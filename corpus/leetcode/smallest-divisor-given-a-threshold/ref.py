import json
import sys


def solve(nums, threshold):
    n = len(nums)
    if threshold < n:
        return -1
    
    lo, hi = 1, max(nums)
    while lo < hi:
        mid = (lo + hi) // 2
        total = 0
        for x in nums:
            total += (x + mid - 1) // mid
            if total > threshold:
                break
        if total <= threshold:
            hi = mid
        else:
            lo = mid + 1
    return lo


CASES = [
    {"nums": [1, 2, 5], "threshold": 8},
    {"nums": [2, 3, 5, 7, 11], "threshold": 11},
    {"nums": [19], "threshold": 1},
    {"nums": [1, 1, 1, 1], "threshold": 4},
    {"nums": [1000000], "threshold": 1},
    {"nums": [12, 5, 7, 9, 11], "threshold": 10},
    {"nums": [5, 5, 5, 5, 5], "threshold": 5},
    {"nums": [1], "threshold": 1},
]


if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        got = solve(nums=case["nums"], threshold=case["threshold"])
        results.append({
            "id": i,
            "input": {
                "nums": case["nums"],
                "threshold": case["threshold"],
            },
            "expected": json.dumps(got, separators=(',', ':'), ensure_ascii=False),
        })
    sys.stdout.write(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
