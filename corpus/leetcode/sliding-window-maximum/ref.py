from collections import deque
import json

def solve(nums: list[int], k: int) -> list[int]:
    n = len(nums)
    if k <= 0 or n < k:
        return []
    if k == 1:
        return list(nums)
    dq = deque()  # stores indices, values are decreasing
    result = []
    for i, v in enumerate(nums):
        # remove indices whose values are <= current from the back
        while dq and nums[dq[-1]] <= v:
            dq.pop()
        dq.append(i)
        # remove front index if it's out of window
        if dq[0] <= i - k:
            dq.popleft()
        # start recording once first window is complete
        if i >= k - 1:
            result.append(nums[dq[0]])
    return result


CASES = [
    {"id": 0, "nums": [1, 3, -1, -3, 5, 3, 6, 7], "k": 3},
    {"id": 1, "nums": [1], "k": 1},
    {"id": 2, "nums": [1, 2, 3], "k": 4},
    {"id": 3, "nums": [4, 4, 4, 4], "k": 2},
    {"id": 4, "nums": [9, 8, 7, 6, 5, 4, 3, 2, 1], "k": 3},
    {"id": 5, "nums": [1, 2, 3, 4, 5], "k": 5},
    {"id": 6, "nums": [7, 2, 4], "k": 2},
    {"id": 7, "nums": [-7, -8, -1, -3, -5, -2, -9], "k": 3},
]


if __name__ == '__main__':
    out = []
    for c in CASES:
        res = solve(c["nums"], c["k"])
        out.append({
            "id": c["id"],
            "input": {"nums": c["nums"], "k": c["k"]},
            "expected": json.dumps(res, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
