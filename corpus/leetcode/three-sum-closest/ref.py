def solve(nums, target):
    nums = sorted(nums)
    n = len(nums)
    best = nums[0] + nums[1] + nums[2]
    for i in range(n - 2):
        lo, hi = i + 1, n - 1
        while lo < hi:
            s = nums[i] + nums[lo] + nums[hi]
            if abs(s - target) < abs(best - target):
                best = s
            if s < target:
                lo += 1
            elif s > target:
                hi -= 1
            else:
                return s
    return best


CASES = [
    {"nums": [1, 2, 5, 6, 8, 11], "target": 13},
    {"nums": [-1, 2, 1, -4], "target": 1},
    {"nums": [0, 0, 0], "target": 1},
    {"nums": [1, 1, 1, 0], "target": -100},
    {"nums": [1, 2, 3, 4, 5], "target": 10},
    {"nums": [-1, 0, 1, 2, -1, -4], "target": 0},
    {"nums": [4, 0, 5, -5, 3, 3, 0, -4, -5], "target": -2},
    {"nums": [1, 2, 3], "target": 6},
]

if __name__ == '__main__':
    import json
    out = []
    for i, case in enumerate(CASES):
        result = solve(case["nums"], case["target"])
        out.append({"id": i, "input": case, "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
