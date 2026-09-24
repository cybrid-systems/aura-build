def solve(s: str, wordDict: list[str]) -> bool:
    n = len(s)
    if n == 0:
        return False
    word_set = set(wordDict)
    if not word_set:
        return False
    max_len = max(len(w) for w in word_set)
    dp = [False] * (n + 1)
    dp[0] = True
    for i in range(1, n + 1):
        start = max(0, i - max_len)
        for j in range(start, i):
            if dp[j] and s[j:i] in word_set:
                dp[i] = True
                break
    return dp[n]


CASES = [
    {"s": "leetcode", "wordDict": ["leet", "code"]},
    {"s": "applepenapple", "wordDict": ["apple", "pen"]},
    {"s": "catsandog", "wordDict": ["cats", "dog", "sand", "and", "cat"]},
    {"s": "a", "wordDict": ["a"]},
    {"s": "a", "wordDict": ["b"]},
    {"s": "abcd", "wordDict": ["a", "abc", "b", "cd"]},
    {"s": "cars", "wordDict": ["car", "ca", "rs"]},
    {"s": "aaaaa", "wordDict": ["aa", "aaa"]},
]


if __name__ == '__main__':
    import json
    results = []
    for idx, case in enumerate(CASES):
        out = solve(case["s"], case["wordDict"])
        results.append({"id": idx, "input": case, "expected": json.dumps(out, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
