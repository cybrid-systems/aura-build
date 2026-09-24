import json

def solve(nums):
    n = len(nums)
    if n == 0:
        return []
    answer = [0] * n
    # First pass: left products
    left = 1
    for i in range(n):
        answer[i] = left
        left *= nums[i]
    # Second pass: right products
    right = 1
    for i in range(n - 1, -1, -1):
        answer[i] *= right
        right *= nums[i]
    return answer

CASES = [
    {"nums": [2, 1, 3, 4]},
    {"nums": [0, 4, 0]},
    {"nums": [-1, 1, 0, -3, 3]},
    {"nums": [1, 2, 3, 4]},
    {"nums": [0, 0]},
    {"nums": [5]},
    {"nums": [-2, -3, 4, -1]},
    {"nums": [1, 0, 2, 0, 3]},
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
