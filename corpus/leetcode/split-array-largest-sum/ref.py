import json
import sys

def split_array_largest_sum(nums, m):
    lo = max(nums)
    hi = sum(nums)
    while lo < hi:
        mid = (lo + hi) // 2
        # greedy: count how many subarrays needed if max sum is mid
        count = 1
        cur = 0
        for x in nums:
            if cur + x <= mid:
                cur += x
            else:
                count += 1
                cur = x
        if count <= m:
            hi = mid
        else:
            lo = mid + 1
    return lo

def solve(nums, m):
    return split_array_largest_sum(nums, m)

CASES = [
    {"nums": [7, 2, 5, 10, 8], "m": 2},
    {"nums": [1, 2, 3, 4, 5], "m": 2},
    {"nums": [1, 4, 4], "m": 3},
    {"nums": [1, 4, 4], "m": 1},
    {"nums": [10, 5, 2, 7, 8, 4, 3, 6], "m": 4},
    {"nums": [5, 1, 4, 5, 1], "m": 2},
    {"nums": [1], "m": 1},
    {"nums": [2, 3, 1, 2, 4, 3, 2, 1, 1], "m": 3},
]

if __name__ == '__main__':
    results = []
    for i, c in enumerate(CASES):
        out = solve(c["nums"], c["m"])
        results.append({
            "id": i,
            "input": c,
            "expected": json.dumps(out, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
