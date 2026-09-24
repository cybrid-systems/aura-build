def solve(nums):
    n = len(nums)
    if n == 0:
        return []
    answer = [1] * n
    # Left products
    left = 1
    for i in range(n):
        answer[i] = left
        left *= nums[i]
    # Right products
    right = 1
    for i in range(n - 1, -1, -1):
        answer[i] *= right
        right *= nums[i]
    return answer


CASES = [
    {"nums": []},
    {"nums": [1]},
    {"nums": [1, 2, 3, 4]},
    {"nums": [-1, 1, 0, -3, 3]},
    {"nums": [0, 0, 1, 2]},
    {"nums": [2, 3, 0, 5]},
    {"nums": [-2, -3, 4, -5]},
    {"nums": [1, 1, 1, 1, 1]},
]


if __name__ == '__main__':
    import json
    out = []
    for i, c in enumerate(CASES):
        result = solve(c["nums"])
        out.append({
            "id": i,
            "input": c,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
