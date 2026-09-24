def solve(s: str, t: str) -> int:
    MOD = 1_000_000_007
    n, m = len(s), len(t)
    if m > n:
        return 0
    # dp[j] = number of distinct subsequences of s processed so far equal to t[:j]
    dp = [0] * (m + 1)
    dp[0] = 1
    for i in range(n):
        # Traverse j from m down to 1 to avoid using the same character multiple times
        for j in range(m, 0, -1):
            if s[i] == t[j - 1]:
                dp[j] = (dp[j] + dp[j - 1]) % MOD
    return dp[m]

CASES = [
    {"s": "rabbbit", "t": "rabbit"},
    {"s": "babgbag", "t": "bag"},
    {"s": "", "t": ""},
    {"s": "", "t": "a"},
    {"s": "a", "t": "a"},
    {"s": "a", "t": "b"},
    {"s": "aa", "t": "a"},
    {"s": "aaa", "t": "aa"},
    {"s": "abcdef", "t": "fed"},
    {"s": "zxyzxyz", "t": "xyz"},
]

if __name__ == '__main__':
    import json
    out = []
    for idx, case in enumerate(CASES):
        result = solve(case["s"], case["t"])
        out.append({"id": idx, "input": case, "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
