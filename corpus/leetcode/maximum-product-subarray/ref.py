import sys
import json

def solve(nums):
    if not nums:
        return 0
    max_prod = nums[0]
    min_prod = nums[0]
    result = nums[0]
    for i in range(1, len(nums)):
        x = nums[i]
        if x < 0:
            max_prod, min_prod = min_prod, max_prod
        max_prod = max(x, max_prod * x)
        min_prod = min(x, min_prod * x)
        if max_prod > result:
            result = max_prod
    return result

CASES = [
    {"nums": [2, 3, -2, 4]},
    {"nums": [-2, 0, -1]},
    {"nums": [-2]},
    {"nums": [0, 2]},
    {"nums": [2, -5, -2, -4, 1]},
    {"nums": [-1, -3, -10, 0, 60]},
    {"nums": [1, -2, 3, -4, 5, -6]},
    {"nums": [0, 0, 0]},
]

if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        result = solve(case["nums"])
        results.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
