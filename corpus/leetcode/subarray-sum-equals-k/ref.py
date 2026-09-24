import json
from collections import defaultdict

def solve(nums, k):
    """Count continuous subarrays summing to k using prefix sum + hashmap."""
    count = 0
    prefix_sum = 0
    freq = defaultdict(int)
    freq[0] = 1
    for num in nums:
        prefix_sum += num
        count += freq[prefix_sum - k]
        freq[prefix_sum] += 1
    return count

CASES = [
    {"nums": [1, 1, 1], "k": 2},
    {"nums": [1, 2, 3], "k": 3},
    {"nums": [1, -1, 1, -1, 1, -1], "k": 0},
    {"nums": [1], "k": 1},
    {"nums": [1], "k": 0},
    {"nums": [0, 0, 0, 0, 0], "k": 0},
    {"nums": [3, 4, 7, 2, -3, 1, 4, 2], "k": 7},
    {"nums": [-1, -1, 1, 1, -1], "k": 0},
]

if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        out = solve(case["nums"], case["k"])
        results.append({
            "id": i,
            "input": case,
            "expected": json.dumps(out, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
