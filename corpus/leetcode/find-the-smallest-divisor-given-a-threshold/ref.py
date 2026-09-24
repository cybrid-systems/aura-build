import json
import math

def solve(nums: list[int], threshold: int) -> int:
    n = len(nums)
    if threshold < n:
        return -1
    lo, hi = 1, max(nums)
    # binary search for smallest divisor with cost <= threshold
    while lo < hi:
        mid = (lo + hi) // 2
        cost = sum((num + mid - 1) // mid for num in nums)
        if cost <= threshold:
            hi = mid
        else:
            lo = mid + 1
    return lo

CASES = [
    {"nums": [1, 2, 5], "threshold": 9},
    {"nums": [2, 1, 0], "threshold": 3},
    {"nums": [1, 1, 1], "threshold": 3},
    {"nums": [100000], "threshold": 1},
    {"nums": [10, 20, 30, 40], "threshold": 5},
    {"nums": [1], "threshold": 1},
    {"nums": [4, 4, 4, 4], "threshold": 4},
    {"nums": [2, 3, 5, 7, 11], "threshold": 8},
]

if __name__ == '__main__':
    out = []
    for i, case in enumerate(CASES):
        nums = case["nums"]
        threshold = case["threshold"]
        result = solve(nums, threshold)
        out.append({
            "id": i,
            "input": {"nums": nums, "threshold": threshold},
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
