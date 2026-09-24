def solve(nums):
    nums = sorted(nums)
    n = len(nums)
    used = [False] * n
    result = []
    path = []
    def backtrack():
        if len(path) == n:
            result.append(path.copy())
            return
        for i in range(n):
            if used[i]:
                continue
            if i > 0 and nums[i] == nums[i-1] and not used[i-1]:
                continue
            used[i] = True
            path.append(nums[i])
            backtrack()
            path.pop()
            used[i] = False
    backtrack()
    return result


CASES = [
    {"nums": [1, 1, 2]},
    {"nums": [0, 1]},
    {"nums": [1, 2, 3]},
    {"nums": [1, 1, 1]},
    {"nums": []},
    {"nums": [1]},
    {"nums": [2, 2, 1, 1]},
    {"nums": [1, 2, 1, 2]},
]

if __name__ == '__main__':
    import json
    out = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        out.append({"id": i, "input": case, "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
