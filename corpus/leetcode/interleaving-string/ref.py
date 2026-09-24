import sys
import json

def solve(s1: str, s2: str, s3: str) -> bool:
    n, m = len(s1), len(s2)
    if n + m != len(s3):
        return False
    if n < m:
        # ensure s1 is the longer one so we optimize space over s2
        s1, s2 = s2, s1
        n, m = m, n
    # dp[j] represents whether s3[:i+j] can be formed from s1[:i] and s2[:j]
    dp = [False] * (m + 1)
    dp[0] = True
    # initialize first row (i=0)
    for j in range(1, m + 1):
        dp[j] = dp[j - 1] and s2[j - 1] == s3[j - 1]
    for i in range(1, n + 1):
        # update column j=0
        dp[0] = dp[0] and s1[i - 1] == s3[i - 1]
        for j in range(1, m + 1):
            from_s1 = dp[j] and s1[i - 1] == s3[i + j - 1]
            from_s2 = dp[j - 1] and s2[j - 1] == s3[i + j - 1]
            dp[j] = from_s1 or from_s2
    return dp[m]

CASES = [
    {"s1": "aabcc", "s2": "dbbca", "s3": "aadbbcbcac"},
    {"s1": "aabcc", "s2": "dbbca", "s3": "aadbbbaccc"},
    {"s1": "", "s2": "", "s3": ""},
    {"s1": "", "s2": "abc", "s3": "abc"},
    {"s1": "", "s2": "abc", "s3": "ab"},
    {"s1": "abc", "s2": "", "s3": "abc"},
    {"s1": "a", "s2": "b", "s3": "ab"},
    {"s1": "a", "s2": "b", "s3": "ba"},
]

if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        result = solve(case["s1"], case["s2"], case["s3"])
        results.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
