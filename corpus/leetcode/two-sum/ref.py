import sys
import json

def solve(nums: list[int], target: int) -> list[int]:
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            idx1, idx2 = seen[complement], i
            return [min(idx1, idx2), max(idx1, idx2)]
        seen[num] = i
    return [-1, -1]


CASES = [
    {"nums": [2, 7, 11, 15], "target": 9},
    {"nums": [3, 2, 4], "target": 6},
    {"nums": [3, 3], "target": 6},
    {"nums": [-1, -2, -3, -4, -5], "target": -8},
    {"nums": [0, 4, 3, 0], "target": 0},
    {"nums": [1, 5, 1, 5], "target": 10},
    {"nums": [1000000, -1000000, 2, 3], "target": 0},
    {"nums": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], "target": 19},
]


def _read_cases_from_stdin():
    data = sys.stdin.read().strip().split()
    if not data:
        return []
    cases = []
    i = 0
    while i < len(data):
        n = int(data[i])
        target = int(data[i + 1])
        i += 2
        nums = [int(x) for x in data[i:i + n]]
        i += n
        cases.append({"nums": nums, "target": target})
    return cases


if __name__ == '__main__':
    results = []
    for idx, case in enumerate(CASES):
        out = solve(case["nums"], case["target"])
        results.append({
            "id": idx,
            "input": case,
            "expected": json.dumps(out, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
