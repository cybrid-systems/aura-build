import sys
import json
from collections import defaultdict

def solve(nums, k):
    if k == 0:
        return 0
    freq = defaultdict(int)
    left = 0
    distinct = 0
    count = 0
    for right in range(len(nums)):
        x = nums[right]
        if freq[x] == 0:
            distinct += 1
        freq[x] += 1
        while distinct > k:
            y = nums[left]
            freq[y] -= 1
            if freq[y] == 0:
                distinct -= 1
            left += 1
        count += (right - left + 1)
    return count

CASES = [
    {"k": 3, "nums": [1, 2, 1, 2, 3]},
    {"k": 2, "nums": [1, 2, 1, 2, 3]},
    {"k": 1, "nums": [1, 2, 1, 2, 3]},
    {"k": 0, "nums": [1, 2, 3]},
    {"k": 5, "nums": [1, 2, 1, 2, 3]},
    {"k": 2, "nums": [1, 1, 1, 1]},
    {"k": 1, "nums": [1, 2, 3, 4, 5]},
    {"k": 3, "nums": [1, 2, 3]},
]

if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        result = solve(case["nums"], case["k"])
        results.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
