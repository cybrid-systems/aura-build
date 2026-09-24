import sys
import json

def solve(s: str) -> int:
    n = len(s)
    if n == 0:
        return 0
    dp = [[0] * n for _ in range(n)]
    for i in range(n):
        dp[i][i] = 1
    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            if s[i] == s[j]:
                if length == 2:
                    dp[i][j] = 2
                else:
                    dp[i][j] = dp[i + 1][j - 1] + 2
            else:
                dp[i][j] = max(dp[i + 1][j], dp[i][j - 1])
    return dp[0][n - 1]

CASES = [
    {"s": "BBABCBCAB"},
    {"s": "a"},
    {"s": ""},
    {"s": "aa"},
    {"s": "ab"},
    {"s": "abcdef"},
    {"s": "AABCDEBAZ"},
    {"s": "aaaaa"},
]

if __name__ == '__main__':
    results = []
    for idx, case in enumerate(CASES):
        s = case["s"]
        ans = solve(s)
        canonical = json.dumps(ans, separators=(',', ':'), ensure_ascii=False)
        results.append({
            "id": idx,
            "input": {"s": s},
            "expected": canonical,
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
