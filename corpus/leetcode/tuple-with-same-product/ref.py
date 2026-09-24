def solve(nums):
    from collections import defaultdict
    n = len(nums)
    cnt = defaultdict(int)
    for i in range(n):
        for j in range(i + 1, n):
            cnt[nums[i] * nums[j]] += 1
    total = 0
    for k in cnt.values():
        if k >= 2:
            total += k * (k - 1) * 8
    return total


CASES = [
    {"nums": [1, 2, 3, 4, 5, 6]},
    {"nums": [2, 3, 4, 6]},
    {"nums": [1, 2, 3]},
    {"nums": [1, 1, 1, 1]},  # distinctness violated by problem, but test edge
    {"nums": [1, 2, 3, 4, 5, 7, 8, 10]},
    {"nums": [1, 2]},
    {"nums": [-2, -3, 1, 6]},
    {"nums": list(range(1, 21))},
]


if __name__ == '__main__':
    import json
    results = []
    for idx, case in enumerate(CASES):
        result = solve(case["nums"])
        results.append({
            "id": idx,
            "input": {"nums": case["nums"]},
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
