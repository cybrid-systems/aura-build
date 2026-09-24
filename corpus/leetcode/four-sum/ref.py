def solve(nums, target):
    n = len(nums)
    if n < 4:
        return []
    nums.sort()
    res = []
    for i in range(n - 3):
        if i > 0 and nums[i] == nums[i - 1]:
            continue
        # Early termination
        if nums[i] + nums[i + 1] + nums[i + 2] + nums[i + 3] > target:
            break
        if nums[i] + nums[n - 3] + nums[n - 2] + nums[n - 1] < target:
            continue
        for j in range(i + 1, n - 2):
            if j > i + 1 and nums[j] == nums[j - 1]:
                continue
            if nums[i] + nums[j] + nums[j + 1] + nums[j + 2] > target:
                break
            if nums[i] + nums[j] + nums[n - 2] + nums[n - 1] < target:
                continue
            lo, hi = j + 1, n - 1
            while lo < hi:
                s = nums[i] + nums[j] + nums[lo] + nums[hi]
                if s == target:
                    res.append([nums[i], nums[j], nums[lo], nums[hi]])
                    lo += 1
                    hi -= 1
                    while lo < hi and nums[lo] == nums[lo - 1]:
                        lo += 1
                    while lo < hi and nums[hi] == nums[hi + 1]:
                        hi -= 1
                elif s < target:
                    lo += 1
                else:
                    hi -= 1
    return res


CASES = [
    {"nums": [1, 0, -1, 0, -2, 2], "target": 0},
    {"nums": [2, 2, 2, 2, 2], "target": 8},
    {"nums": [], "target": 0},
    {"nums": [1, 2, 3, 4], "target": 10},
    {"nums": [-3, -2, -1, 0, 0, 1, 2, 3], "target": 0},
    {"nums": [0, 0, 0, 0, 0], "target": 0},
    {"nums": [1, -2, -5, -4, -3, 3, 3, 5], "target": -11},
    {"nums": list(range(-5, 6)), "target": 0},
]


if __name__ == '__main__':
    import json
    out = []
    for idx, case in enumerate(CASES):
        result = solve(**case)
        out.append({
            "id": idx,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
