def solve(nums: list[int], x: int) -> int:
    if x == 0:
        return 0
    total = sum(nums)
    if total < x:
        return -1
    target = total - x
    if target == 0:
        return len(nums)
    
    best = -1
    current = 0
    left = 0
    for right, val in enumerate(nums):
        current += val
        while current > target and left <= right:
            current -= nums[left]
            left += 1
        if current == target:
            best = max(best, right - left + 1)
    
    if best == -1:
        return -1
    return len(nums) - best


CASES = [
    {"nums": [1, 1, 3, 2, 4], "x": 5},
    {"nums": [5, 6, 7, 8, 9], "x": 4},
    {"nums": [3, 2, 20, 1, 1, 3], "x": 10},
    {"nums": [], "x": 0},
    {"nums": [], "x": 5},
    {"nums": [1, 2, 3], "x": 0},
    {"nums": [1, 2, 3], "x": 6},
    {"nums": [0, 0, 0, 0], "x": 0},
    {"nums": [1], "x": 1},
    {"nums": [1], "x": 2},
    {"nums": [1, 2, 3, 4, 5], "x": 15},
]


if __name__ == '__main__':
    import json
    out = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        out.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
