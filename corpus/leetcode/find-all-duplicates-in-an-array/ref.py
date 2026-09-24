def solve(nums):
    result = []
    for x in nums:
        idx = abs(x) - 1
        if nums[idx] < 0:
            result.append(abs(x))
        else:
            nums[idx] = -nums[idx]
    return result

CASES = [
    {"nums": [4, 3, 2, 7, 8, 2, 3, 1]},
    {"nums": [1, 1, 2]},
    {"nums": [1]},
    {"nums": [2, 2]},
    {"nums": [3, 1, 3, 4, 2, 5]},
    {"nums": [5, 4, 3, 2, 1, 5, 4, 3, 2, 1]},
    {"nums": [10, 2, 5, 10, 9, 1, 1, 4, 3, 7]},
    {"nums": list(range(1, 101)) + [50, 75]},
]

if __name__ == '__main__':
    import json
    out = []
    for i, case in enumerate(CASES):
        # deep copy the list so each case is independent
        inp = list(case["nums"])
        result = solve(inp)
        out.append({"id": i, "input": case, "expected": json.dumps(sorted(result), separators=(',', ':'))})
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
