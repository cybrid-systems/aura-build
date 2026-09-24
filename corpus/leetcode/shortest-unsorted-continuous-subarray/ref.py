import json

def solve(nums):
    n = len(nums)
    if n < 2:
        return 0
    
    # Find left boundary: first index where nums[i] > min of suffix starting at i+1
    left = -1
    suffix_min = nums[-1]
    for i in range(n - 2, -1, -1):
        if nums[i] > suffix_min:
            left = i
        suffix_min = min(suffix_min, nums[i])
    
    if left == -1:
        return 0
    
    # Find right boundary: first index where nums[i] < max of prefix ending at i-1
    right = -1
    prefix_max = nums[0]
    for i in range(1, n):
        if nums[i] < prefix_max:
            right = i
        prefix_max = max(prefix_max, nums[i])
    
    return right - left + 1

CASES = [
    {"nums": [2, 6, 4, 8, 10, 9, 15]},
    {"nums": [1, 2, 3, 4]},
    {"nums": [1]},
    {"nums": [2, 1]},
    {"nums": [1, 3, 2, 4]},
    {"nums": [5, 4, 3, 2, 1]},
    {"nums": [1, 2, 3, 5, 4]},
    {"nums": [-1, 0, -2, -3]},
]

if __name__ == '__main__':
    results = []
    for idx, case in enumerate(CASES):
        out = solve(**case)
        results.append({"id": idx, "input": case, "expected": json.dumps(out, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
