import sys
import json

def solve(nums):
    ones = 0
    twos = 0
    for x in nums:
        ones = (ones ^ x) & ~twos
        twos = (twos ^ x) & ~ones
    return ones

CASES = [
    {"nums": [2, 2, 3, 2]},
    {"nums": [0, 1, 0, 1, 0, 1, 99]},
    {"nums": [-5, -5, -5, -3]},
    {"nums": [1]},
    {"nums": [7, 7, 7, 5, 5, 5, 9]},
    {"nums": [4, 4, 4, 4, 4, 4, 42]},
    {"nums": [-1, -1, -1, 2]},
    {"nums": [3, 3, 3, -3, -3, -3, 8, 8, 8, 100]},
]

if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        out = solve(**case)
        results.append({
            "id": i,
            "input": case,
            "expected": json.dumps(out, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
