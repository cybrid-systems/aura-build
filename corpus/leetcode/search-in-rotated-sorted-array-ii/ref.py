import json
from urllib.parse import unquote

def solve(nums, target):
    left, right = 0, len(nums) - 1
    while left <= right:
        mid = (left + right) // 2
        if nums[mid] == target:
            return True
        if nums[left] == nums[mid] == nums[right]:
            left += 1
            right -= 1
            continue
        if nums[left] <= nums[mid]:
            if nums[left] <= target < nums[mid]:
                right = mid - 1
            else:
                left = mid + 1
        else:
            if nums[mid] < target <= nums[right]:
                left = mid + 1
            else:
                right = mid - 1
    return False

CASES = [
    {"nums": [4, 5, 6, 7, 0, 1, 2], "target": 0},
    {"nums": [4, 5, 6, 7, 0, 1, 2], "target": 3},
    {"nums": [2, 5, 6, 0, 0, 1, 2], "target": 0},
    {"nums": [2, 5, 6, 0, 0, 1, 2], "target": 3},
    {"nums": [1], "target": 0},
    {"nums": [1], "target": 1},
    {"nums": [], "target": 5},
    {"nums": [1, 1, 1, 1, 1], "target": 1},
    {"nums": [1, 1, 1, 1, 1], "target": 2},
    {"nums": [3, 1], "target": 1},
]

if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        out = solve(case["nums"], case["target"])
        results.append({"id": i, "input": case, "expected": json.dumps(out, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
