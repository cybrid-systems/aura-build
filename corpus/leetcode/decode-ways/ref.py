import sys
import json

MOD = 10**9 + 7

def num_decodings(s: str) -> int:
    if not s or s[0] == '0':
        return 0
    n = len(s)
    # dp_prev2 = dp[i-2], dp_prev1 = dp[i-1]
    dp_prev2 = 1  # dp[0]
    dp_prev1 = 1  # dp[1] - since s[0] != '0', there's exactly 1 way to decode first char
    for i in range(1, n):
        curr = 0
        # Single digit decode
        if s[i] != '0':
            curr += dp_prev1
        # Two digit decode
        two = int(s[i-1:i+1])
        if 10 <= two <= 26:
            curr += dp_prev2
        curr %= MOD
        dp_prev2, dp_prev1 = dp_prev1, curr
    return dp_prev1

def solve(s: str) -> int:
    return num_decodings(s)

CASES = [
    {"s": "12"},
    {"s": "226"},
    {"s": "06"},
    {"s": "0"},
    {"s": "27"},
    {"s": "1111111111"},
    {"s": "1"},
    {"s": "10"},
]

if __name__ == '__main__':
    results = []
    for idx, case in enumerate(CASES):
        result = solve(**case)
        results.append({
            "id": idx,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
