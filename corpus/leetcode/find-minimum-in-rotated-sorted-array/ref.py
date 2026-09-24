import json

def solve(nums):
    lo, hi = 0, len(nums) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if nums[mid] > nums[hi]:
            lo = mid + 1
        else:
            hi = mid
    return nums[lo]

CASES = [
    {"nums": [3, 1, 2]},
    {"nums": [4, 5, 6, 7, 0, 1, 2]},
    {"nums": [11, 13, 15, 17]},
    {"nums": [2, 1]},
    {"nums": [1]},
    {"nums": [5, 6, 7, 8, 9, 1, 2, 3, 4]},
    {"nums": [2, 3, 4, 5, 6, 7, 8, 9, 1]},
    {"nums": [4, 5, 1, 2, 3]},
    {"nums": [1, 2, 3, 4, 5]},
    {"nums": list(range(1000))[-500:] + list(range(1000))[:500]},
]

if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        out = solve(**case)
        results.append({
            "id": i,
            "input": case,
            "expected": json.dumps(out, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
