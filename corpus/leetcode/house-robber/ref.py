def solve(nums: list[int]) -> int:
    if not nums:
        return 0
    prev2 = 0
    prev1 = 0
    for amount in nums:
        current = max(prev1, prev2 + amount)
        prev2 = prev1
        prev1 = current
    return prev1


CASES = [
    {"nums": []},
    {"nums": [0]},
    {"nums": [1]},
    {"nums": [1, 2]},
    {"nums": [2, 1]},
    {"nums": [1, 2, 3, 1]},
    {"nums": [2, 7, 9, 3, 1]},
    {"nums": [5, 1, 1, 5]},
    {"nums": [0, 0, 0, 0]},
    {"nums": [10, 1, 1, 10, 1, 1, 10]},
    {"nums": [4, 1, 1, 4, 1, 1, 4, 1, 1, 4]},
    {"nums": list(range(100))},
]


if __name__ == '__main__':
    import json
    results = []
    for idx, case in enumerate(CASES):
        got = solve(**case)
        results.append({"id": idx, "input": case, "expected": json.dumps(got, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(results, ensure_ascii=False))
