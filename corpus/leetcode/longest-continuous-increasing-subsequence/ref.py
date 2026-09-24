import json
import sys
from typing import List

def solve(nums: List[int]) -> int:
    if not nums:
        return 0
    longest = 1
    current = 1
    for i in range(1, len(nums)):
        if nums[i] > nums[i-1]:
            current += 1
        else:
            current = 1
        if current > longest:
            longest = current
    return longest

CASES = [
    {"nums": [1, 2, 3, 2, 4, 5]},
    {"nums": [5, 4, 3, 2, 1]},
    {"nums": [7]},
    {"nums": []},
    {"nums": [1, 2, 3, 4, 5]},
    {"nums": [1, 1, 1, 1]},
    {"nums": [1, 2, 2, 3, 4, 5]},
    {"nums": [-3, -2, -1, 0, 1, 2]},
]

def _to_json(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return json.dumps(v)
    if isinstance(v, list):
        return json.dumps(v, separators=(',', ':'), ensure_ascii=False)
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=False)
    return json.dumps(v, separators=(',', ':'), ensure_ascii=False)

if __name__ == '__main__':
    out = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        out.append({
            "id": i,
            "input": case,
            "expected": _to_json(result)
        })
    sys.stdout.write(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
