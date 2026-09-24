import json

MOD = 10**9 + 7

def solve(nums, target):
    """Count ordered sequences from nums (with repetition) summing to target."""
    nums = list(nums)
    dp = [0] * (target + 1)
    dp[0] = 1  # empty sequence sums to 0
    for i in range(1, target + 1):
        total = 0
        for num in nums:
            if i - num >= 0:
                total += dp[i - num]
        dp[i] = total % MOD
    return dp[target]

CASES = [
    {"id": 0, "nums": [1, 2, 3], "target": 4},
    {"id": 1, "nums": [9], "target": 3},
    {"id": 2, "nums": [1], "target": 4},
    {"id": 3, "nums": [1, 2], "target": 3},
    {"id": 4, "nums": [2], "target": 10},
    {"id": 5, "nums": [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20], "target": 100},
    {"id": 6, "nums": [1], "target": 1},
    {"id": 7, "nums": [1, 2, 3], "target": 1},
]

if __name__ == '__main__':
    results = []
    for case in CASES:
        cid = case["id"]
        inp = {"nums": case["nums"], "target": case["target"]}
        result = solve(case["nums"], case["target"])
        results.append({
            "id": cid,
            "input": inp,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
