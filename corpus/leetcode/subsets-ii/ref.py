def subsetsWithDup(nums):
    nums = sorted(nums)
    res = []
    n = len(nums)
    
    def backtrack(start, path):
        # Add current subset
        res.append(path[:])
        for i in range(start, n):
            # Skip duplicates: if current element equals previous AND we're not at the start of this level
            if i > start and nums[i] == nums[i - 1]:
                continue
            path.append(nums[i])
            backtrack(i + 1, path)
            path.pop()
    
    backtrack(0, [])
    return res


def solve(nums):
    return subsetsWithDup(nums)


CASES = [
    {"nums": [1, 2, 2]},
    {"nums": [0]},
    {"nums": [1, 2, 3]},
    {"nums": [1, 1, 1]},
    {"nums": [2, 1, 2]},
    {"nums": [-1, 0, 1]},
    {"nums": [1]},
    {"nums": [5, 5, 5, 5]},
]


if __name__ == '__main__':
    import json
    out = []
    for i, c in enumerate(CASES):
        result = solve(**c)
        expected = sorted([sorted(s) for s in result])
        out.append({
            "id": i,
            "input": c,
            "expected": json.dumps(expected, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
