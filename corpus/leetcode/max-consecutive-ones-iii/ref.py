def solve(nums: list[int], k: int) -> int:
    left = 0
    zeros = 0
    best = 0
    for right, v in enumerate(nums):
        if v == 0:
            zeros += 1
        while zeros > k:
            if nums[left] == 0:
                zeros -= 1
            left += 1
        best = max(best, right - left + 1)
    return best


CASES = [
    {"nums": [1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 0], "k": 2},
    {"nums": [0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 0, 1, 1, 1, 0], "k": 3},
    {"nums": [0, 0, 0, 0], "k": 0},
    {"nums": [0, 0, 0, 0], "k": 4},
    {"nums": [1, 1, 1, 1], "k": 0},
    {"nums": [], "k": 0},
    {"nums": [0, 1, 0, 1, 0, 1, 0, 1], "k": 1},
    {"nums": [0, 1, 0, 1, 0, 1, 0, 1], "k": 2},
]


if __name__ == '__main__':
    import json
    out = []
    for i, c in enumerate(CASES):
        res = solve(c["nums"], c["k"])
        out.append({"id": i, "input": c, "expected": json.dumps(res, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(out, ensure_ascii=False))
