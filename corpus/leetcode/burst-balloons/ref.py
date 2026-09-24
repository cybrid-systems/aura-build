from typing import List
import json

def solve(nums: List[int]) -> int:
    if not nums:
        return 0
    n = len(nums)
    # Pad with 1s on both ends
    a = [1] + nums + [1]
    size = n + 2
    # dp[i][j] = max coins for bursting all balloons in (i, j) exclusive
    dp = [[0] * size for _ in range(size)]
    # length of the interval (exclusive endpoints)
    for length in range(2, size):
        for i in range(0, size - length):
            j = i + length
            best = 0
            ai = a[i]
            aj = a[j]
            # k is the last balloon burst in (i, j)
            for k in range(i + 1, j):
                coins = dp[i][k] + dp[k][j] + ai * a[k] * aj
                if coins > best:
                    best = coins
            dp[i][j] = best
    return dp[0][size - 1]

CASES = [
    {"nums": []},
    {"nums": [1]},
    {"nums": [3, 1, 5]},
    {"nums": [1, 5]},
    {"nums": [7, 9, 8, 0, 0]},
    {"nums": [3, 1, 5, 8]},
    {"nums": [0, 0, 0, 0]},
    {"nums": [5, 5, 5, 5, 5]},
]

if __name__ == '__main__':
    out = []
    for idx, case in enumerate(CASES):
        result = solve(case["nums"])
        out.append({
            "id": idx,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
