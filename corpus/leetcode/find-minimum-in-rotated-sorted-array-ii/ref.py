def solve(nums: list[int]) -> int:
    lo, hi = 0, len(nums) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if nums[mid] > nums[hi]:
            lo = mid + 1
        elif nums[mid] < nums[hi]:
            hi = mid
        else:
            hi -= 1
    return lo


CASES = [
    {"nums": [1, 3, 5, 7, 9]},
    {"nums": [2, 2, 2, 0, 1]},
    {"nums": [5, 5, 5, 5, 5]},
    {"nums": [3, 1, 2, 3, 3]},
    {"nums": [1]},
    {"nums": [2, 1]},
    {"nums": [1, 2, 3]},
    {"nums": [3, 3, 1, 3]},
    {"nums": [10, 1, 10, 10, 10]},
    {"nums": [4, 4, 4, 0, 4, 4, 4]},
]


if __name__ == '__main__':
    import json

    results = []
    for idx, case in enumerate(CASES):
        nums = case["nums"]
        i = solve(nums)
        results.append({
            "id": idx,
            "input": {"nums": nums},
            "expected": json.dumps(int(i), separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
