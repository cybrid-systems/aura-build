def solve(nums):
    lo, mid, hi = 0, 0, len(nums) - 1
    while mid <= hi:
        v = nums[mid]
        if v == 0:
            nums[lo], nums[mid] = nums[mid], nums[lo]
            lo += 1
            mid += 1
        elif v == 1:
            mid += 1
        else:
            nums[mid], nums[hi] = nums[hi], nums[mid]
            hi -= 1
    return nums


CASES = [
    {"nums": [2, 0, 2, 1, 1, 0]},
    {"nums": [2, 0, 1]},
    {"nums": [0]},
    {"nums": [1, 1, 1, 0, 0, 2, 2]},
    {"nums": [2, 2, 2, 2]},
    {"nums": [0, 0, 0, 0]},
    {"nums": [1]},
    {"nums": []},
]


if __name__ == "__main__":
    import json
    out = []
    for i, case in enumerate(CASES):
        # work on a copy so we don't mutate between runs
        arg = list(case["nums"])
        result = solve(arg)
        out.append({"id": i, "input": case, "expected": json.dumps(result, separators=(",", ":"), ensure_ascii=False)})
    print(json.dumps(out, separators=(",", ":"), ensure_ascii=False))
