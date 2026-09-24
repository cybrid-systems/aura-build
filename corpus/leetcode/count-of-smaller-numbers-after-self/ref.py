from typing import List
import json
from bisect import bisect_left

def solve(nums: List[int]) -> List[int]:
    if not nums:
        return []
    # Coordinate compression
    sorted_unique = sorted(set(nums))
    # BIT for frequencies of values seen so far from the right
    size = len(sorted_unique)
    bit = [0] * (size + 1)

    def update(i):
        i += 1
        while i <= size:
            bit[i] += 1
            i += i & -i

    def query(i):
        # sum of [0..i]
        i += 1
        s = 0
        while i > 0:
            s += bit[i]
            i -= i & -i
        return s

    res = []
    # Traverse from right to left
    for x in reversed(nums):
        # count of elements strictly less than x seen so far
        idx = bisect_left(sorted_unique, x)
        if idx == 0:
            res.append(0)
        else:
            res.append(query(idx - 1))
        update(idx)

    return res[::-1]

CASES = [
    {"nums": [5, 2, 6, 1]},
    {"nums": [-1]},
    {"nums": [-1, -1]},
    {"nums": []},
    {"nums": [1, 2, 3, 4, 5]},
    {"nums": [5, 4, 3, 2, 1]},
    {"nums": [2, 0, 1]},
    {"nums": [1, 1, 1, 1]},
]

if __name__ == '__main__':
    out = []
    for i, c in enumerate(CASES):
        result = solve(c["nums"])
        out.append({"id": i, "input": c, "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
