def solve(nums, k):
    if k <= 1:
        return 0
    n = len(nums)
    count = 0
    prod = 1
    left = 0
    for right in range(n):
        prod *= nums[right]
        while prod >= k and left <= right:
            prod //= nums[left]
            left += 1
        count += (right - left + 1)
    return count


CASES = [
    {"nums": [10, 5, 2, 6], "k": 100},
    {"nums": [1, 2, 3], "k": 0},
    {"nums": [2, 1, 1], "k": 6},
    {"nums": [1, 1, 1], "k": 2},
    {"nums": [10, 5, 2, 6], "k": 1},
    {"nums": [1], "k": 2},
    {"nums": [100, 100], "k": 10000},
    {"nums": [10, 10, 10, 10], "k": 1001},
]


if __name__ == '__main__':
    import json
    results = []
    for i, case in enumerate(CASES):
        out = solve(case["nums"], case["k"])
        results.append({
            "id": i,
            "input": {"nums": case["nums"], "k": case["k"]},
            "expected": json.dumps(out, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
