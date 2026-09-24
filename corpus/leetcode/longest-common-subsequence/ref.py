import os
import json

def solve(s: str, t: str) -> int:
    n = len(t)
    dp = [0] * (n + 1)
    for a in s:
        prev = 0
        for j in range(n):
            cur = dp[j + 1]
            if a == t[j]:
                dp[j + 1] = prev + 1
            else:
                if dp[j] > dp[j + 1]:
                    dp[j + 1] = dp[j]
            prev = cur
    return dp[n]

CASES = [
    {"s": "ABCBDAB", "t": "BDBACA"},
    {"s": "A", "t": "A"},
    {"s": "ABC", "t": "DEF"},
    {"s": "AGGTAB", "t": "GXTXAYB"},
    {"s": "AAA", "t": "AA"},
    {"s": "ABCDEF", "t": "ABCDEF"},
    {"s": "AB", "t": "BA"},
    {"s": "ZXVYZWQ", "t": "ZYZWXRQ"},
]

if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        expected = solve(case["s"], case["t"])
        results.append({
            "id": i,
            "input": case,
            "expected": json.dumps(expected, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, ensure_ascii=False))
