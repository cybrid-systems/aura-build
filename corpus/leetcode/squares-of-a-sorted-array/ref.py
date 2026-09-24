import json
import sys
from io import StringIO

def solve(nums):
    n = len(nums)
    result = [0] * n
    left, right = 0, n - 1
    pos = n - 1
    while left <= right:
        lsq = nums[left] * nums[left]
        rsq = nums[right] * nums[right]
        if lsq > rsq:
            result[pos] = lsq
            left += 1
        else:
            result[pos] = rsq
            right -= 1
        pos -= 1
    return result

CASES = [
    {"nums": [1, 2, 3, 4]},
    {"nums": [-4, -1, 0, 3, 10]},
    {"nums": [-5, -3, -2, -1]},
    {"nums": []},
    {"nums": [-7, -3, 2, 3, 11]},
    {"nums": [-1]},
    {"nums": [-3, -3, -2, -2]},
    {"nums": [0, 0, 0, 1, 2]},
]

if __name__ == '__main__':
    out = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        out.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
