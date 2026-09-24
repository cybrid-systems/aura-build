def solve(s: str, p: str) -> bool:
    n, m = len(s), len(p)
    # dp[j] = True if p[:j] matches s[:i] for current i
    dp = [False] * (m + 1)
    dp[0] = True
    # Initialize for i=0: pattern matching empty string
    for j in range(1, m + 1):
        if p[j-1] == '*':
            dp[j] = dp[j-1]
        else:
            dp[j] = False
    
    for i in range(1, n + 1):
        new_dp = [False] * (m + 1)
        for j in range(1, m + 1):
            if p[j-1] == '*':
                # '*' matches empty (dp[j-1] but that's old dp[j-1] which is new_dp[j-1]) 
                # or matches one more char (dp[j] from previous row)
                new_dp[j] = new_dp[j-1] or dp[j]
            elif p[j-1] == '?' or p[j-1] == s[i-1]:
                new_dp[j] = dp[j-1]
            else:
                new_dp[j] = False
        dp = new_dp
    
    return dp[m]


CASES = [
    {"s": "aa", "p": "a"},
    {"s": "aa", "p": "*"},
    {"s": "cb", "p": "?a"},
    {"s": "cb", "p": "?a*"},
    {"s": "", "p": ""},
    {"s": "", "p": "*"},
    {"s": "abc", "p": "a*c"},
    {"s": "abc", "p": "*a*b*c*"},
    {"s": "abcd", "p": "a*d"},
    {"s": "a", "p": "**"},
    {"s": "ho", "p": "**ho**"},
    {"s": "aaa", "p": "a*a"},
    {"s": "aaa", "p": "*a"},
]


if __name__ == '__main__':
    import json
    results = []
    for idx, case in enumerate(CASES):
        result = solve(case["s"], case["p"])
        results.append({
            "id": idx,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
