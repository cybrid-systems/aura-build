import json
from typing import List

MOD = 1_000_000_007

def solve(arr: List[int]) -> int:
    n = len(arr)
    if n == 0:
        return 0
    left = [0] * n
    right = [0] * n
    stack = []
    # Previous less: strictly less
    for i in range(n):
        while stack and arr[stack[-1]] >= arr[i]:
            stack.pop()
        left[i] = stack[-1] if stack else -1
        stack.append(i)
    stack.clear()
    # Next less-or-equal
    for i in range(n - 1, -1, -1):
        while stack and arr[stack[-1]] > arr[i]:
            stack.pop()
        right[i] = stack[-1] if stack else n
        stack.append(i)
    total = 0
    for i in range(n):
        count = (i - left[i]) * (right[i] - i)
        total = (total + (arr[i] % MOD) * count) % MOD
    return total

CASES = [
    {"arr": [3, 1, 2, 4]},
    {"arr": [1, 2, 3, 4]},
    {"arr": [4, 3, 2, 1]},
    {"arr": [2, 1, 3, 1]},
    {"arr": [5]},
    {"arr": [-1, -2, -3]},
    {"arr": [0, 0, 0]},
    {"arr": [1000000000, -1000000000, 0]},
]

if __name__ == '__main__':
    out = []
    for idx, case in enumerate(CASES):
        expected = solve(**case)
        out.append({
            "id": idx,
            "input": case,
            "expected": json.dumps(expected, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
