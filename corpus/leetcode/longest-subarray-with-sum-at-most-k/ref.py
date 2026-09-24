def solve(nums, k):
    left = 0
    curr_sum = 0
    best = 0
    for right in range(len(nums)):
        curr_sum += nums[right]
        while left <= right and curr_sum > k:
            curr_sum -= nums[left]
            left += 1
        if curr_sum <= k:
            length = right - left + 1
            if length > best:
                best = length
    return best


CASES = [
    {"nums": [1, 2, 3, 4, 5], "k": 8},
    {"nums": [1, 2, 3, 4, 5], "k": 15},
    {"nums": [5, 5, 5, 5, 5], "k": 10},
    {"nums": [1, 1, 1, 1, 1], "k": 3},
    {"nums": [], "k": 5},
    {"nums": [0, 0, 0, 0], "k": -1},
    {"nums": [3], "k": 3},
    {"nums": [4], "k": 3},
    {"nums": [2, 2, 2, 2, 2], "k": 0},
]


if __name__ == '__main__':
    import json
    out = []
    for i, case in enumerate(CASES):
        result = solve(case["nums"], case["k"])
        expected = json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        out.append({"id": i, "input": case, "expected": expected})
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
