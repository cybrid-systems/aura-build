def solve(nums):
    result = []
    n = len(nums)
    
    def backtrack(start, current):
        result.append(current[:])
        for i in range(start, n):
            current.append(nums[i])
            backtrack(i + 1, current)
            current.pop()
    
    backtrack(0, [])
    return result


CASES = [
    {"nums": [1, 2, 3]},
    {"nums": [0]},
    {"nums": []},
    {"nums": [1]},
    {"nums": [1, 2]},
    {"nums": [1, 2, 3, 4]},
    {"nums": [-1, 0, 1]},
]


if __name__ == '__main__':
    import json
    output = []
    for idx, case in enumerate(CASES):
        result = solve(**case)
        output.append({"id": idx, "input": case, "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(output, separators=(',', ':'), ensure_ascii=False))
