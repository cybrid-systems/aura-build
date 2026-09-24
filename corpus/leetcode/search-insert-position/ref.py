def solve(nums: list[int], target: int) -> int:
    lo, hi = 0, len(nums)
    while lo < hi:
        mid = (lo + hi) // 2
        if nums[mid] < target:
            lo = mid + 1
        else:
            hi = mid
    return lo


CASES = [
    {"nums": [1, 3, 5, 6], "target": 5},
    {"nums": [1, 3, 5, 6], "target": 2},
    {"nums": [1, 3, 5, 6], "target": 7},
    {"nums": [1, 3, 5, 6], "target": 0},
    {"nums": [1], "target": 0},
    {"nums": [1], "target": 1},
    {"nums": [1], "target": 2},
    {"nums": [], "target": 0},
]


if __name__ == '__main__':
    import json
    results = []
    for i, case in enumerate(CASES):
        out = solve(**case)
        results.append({
            "id": i,
            "input": case,
            "expected": json.dumps(out, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
