import json
import sys

def solve(nums):
    """Find the maximum subarray sum using Kadane's algorithm."""
    current_max = global_max = nums[0]
    for x in nums[1:]:
        current_max = max(x, current_max + x)
        global_max = max(global_max, current_max)
    return global_max


CASES = [
    {"nums": [1, -2, 3, -1, 2, -1, 5, -4]},
    {"nums": [-1]},
    {"nums": [-2, -3, -1, -5]},
    {"nums": [5]},
    {"nums": [1, 2, 3, 4, 5]},
    {"nums": [-1, 2, -3, 4, -1, 2, 1, -5, 4]},
    {"nums": [0, 0, 0, 0]},
    {"nums": [2, -1, 2, -1, 2, -1, 2]},
]


if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        nums = case["nums"]
        out = solve(nums)
        results.append({
            "id": i,
            "input": {"nums": nums},
            "expected": json.dumps(out, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
