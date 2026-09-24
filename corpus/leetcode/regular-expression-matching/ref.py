import json

def solve(s: str, p: str) -> bool:
    m, n = len(s), len(p)
    # dp[i][j] = True if s[i:] matches p[j:]
    dp = [[False] * (n + 1) for _ in range(m + 1)]
    dp[m][n] = True  # empty matches empty
    
    # Fill from bottom-right
    for i in range(m, -1, -1):
        for j in range(n - 1, -1, -1):
            first_match = (i < m) and (p[j] == s[i] or p[j] == '.')
            if j + 1 < n and p[j + 1] == '*':
                # x* case: skip x* OR use x and stay on same pattern position
                dp[i][j] = dp[i][j + 2] or (first_match and dp[i + 1][j])
            else:
                dp[i][j] = first_match and dp[i + 1][j + 1]
    
    return dp[0][0]


CASES = [
    {"s": "aa",      "p": "a"},
    {"s": "aa",      "p": "a*"},
    {"s": "ab",      "p": ".*"},
    {"s": "aab",     "p": "c*a*b"},
    {"s": "mississippi", "p": "mis*is*p*."},
    {"s": "",        "p": ""},
    {"s": "",        "p": "a*"},
    {"s": "ab",      "p": ".*c"},
    {"s": "aaa",     "p": "a*a"},
    {"s": "a",       "p": "ab*"},
]


if __name__ == '__main__':
    out = []
    for idx, case in enumerate(CASES):
        result = solve(case["s"], case["p"])
        out.append({
            "id": idx,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
