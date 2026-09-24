def solve(nums: list[int], target: int) -> int:
    total = sum(nums)
    # Check feasibility
    if abs(target) > total:
        return 0
    if (total + target) % 2 != 0:
        return 0
    P = (total + target) // 2
    if P < 0:
        return 0

    # Count subsets with sum == P using 1D DP
    dp = [0] * (P + 1)
    dp[0] = 1
    for num in nums:
        # Traverse backwards to avoid using an element twice
        for s in range(P, num - 1, -1):
            dp[s] += dp[s - num]
    return dp[P]


CASES = [
    {"nums": [1, 1, 1, 1, 1], "target": 3},
    {"nums": [1, 1, 1, 1, 1], "target": 5},
    {"nums": [1, 1, 1, 1, 1], "target": -3},
    {"nums": [1], "target": 1},
    {"nums": [1], "target": -1},
    {"nums": [0, 0, 0, 0, 0, 0, 0, 0, 1], "target": 1},
    {"nums": [1000] * 20, "target": 0},
    {"nums": [1, 2, 3, 4, 5], "target": 3},
]


if __name__ == '__main__':
    import json
    results = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        results.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
