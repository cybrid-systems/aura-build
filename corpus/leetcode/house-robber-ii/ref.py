import sys, json

def rob_linear(arr):
    if not arr:
        return 0
    if len(arr) == 1:
        return arr[0]
    prev2, prev1 = 0, 0
    for x in arr:
        prev2, prev1 = prev1, max(prev1, prev2 + x)
    return prev1

def solve(nums):
    n = len(nums)
    if n == 0:
        return 0
    if n == 1:
        return nums[0]
    return max(rob_linear(nums[:-1]), rob_linear(nums[1:]))

CASES = [
    {"nums": [2, 3, 2]},
    {"nums": [1, 2, 3, 1]},
    {"nums": [0]},
    {"nums": [1]},
    {"nums": [1, 2]},
    {"nums": [2, 3, 2, 5, 8, 1]},
    {"nums": [0, 0, 0, 0]},
    {"nums": [10, 1, 1, 10, 1, 1, 10]},
]

if __name__ == '__main__':
    out = []
    for i, c in enumerate(CASES):
        res = solve(c["nums"])
        out.append({"id": i, "input": c, "expected": json.dumps(res, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
