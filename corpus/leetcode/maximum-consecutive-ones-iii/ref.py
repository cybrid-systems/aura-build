def solve(nums: list[int], k: int) -> int:
    left = 0
    zero_count = 0
    best = 0
    for right, val in enumerate(nums):
        if val == 0:
            zero_count += 1
        while zero_count > k:
            if nums[left] == 0:
                zero_count -= 1
            left += 1
        best = max(best, right - left + 1)
    return best


CASES = [
    {"nums": [1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 0], "k": 2},
    {"nums": [0, 0, 1, 1, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 0], "k": 3},
    {"nums": [1, 1, 1, 1], "k": 0},
    {"nums": [0, 0, 0, 0], "k": 0},
    {"nums": [0, 0, 0, 0], "k": 4},
    {"nums": [1, 0, 1, 0, 1, 0, 1], "k": 1},
    {"nums": [0, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 0], "k": 2},
    {"nums": [1], "k": 0},
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
