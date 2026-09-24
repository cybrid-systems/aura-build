from typing import List
import json


def solve(nums: List[int]) -> List[int]:
    n = len(nums)
    if n == 0:
        return []
    if n == 1:
        return [-1]

    result = [-1] * n
    stack = []  # stores indices, values are monotonically decreasing from bottom to top

    # Traverse twice to handle circular wrap-around
    for i in range(2 * n):
        real_idx = i % n
        while stack and nums[real_idx] > nums[stack[-1]]:
            prev_idx = stack.pop()
            # Only set if not already assigned (first greater wins since we want smallest j != i)
            if result[prev_idx] == -1:
                result[prev_idx] = nums[real_idx]
        if i < n:
            stack.append(real_idx)

    return result


CASES = [
    {"nums": [1, 2, 1]},
    {"nums": [1, 2, 3, 4, 3]},
    {"nums": []},
    {"nums": [5]},
    {"nums": [5, 4, 3, 2, 1]},
    {"nums": [1, 3, 2, 4]},
    {"nums": [2, 2, 2, 2]},
    {"nums": [3, 1, 2, 5, 4]},
]


if __name__ == '__main__':
    out = []
    for i, c in enumerate(CASES):
        result = solve(c["nums"])
        out.append({
            "id": i,
            "input": {"nums": c["nums"]},
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
