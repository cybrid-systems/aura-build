def solve(s, word_dict):
    word_set = set(word_dict)
    n = len(s)
    max_len = max((len(w) for w in word_set), default=0)

    # Memoization: dp[i] = list of sentences for suffix s[i:]
    memo = {}
    def helper(i):
        if i in memo:
            return memo[i]
        if i == n:
            memo[i] = [""]
            return memo[i]
        results = []
        # Try each word length up to max_len (or remaining length)
        for L in range(1, min(max_len, n - i) + 1):
            word = s[i:i+L]
            if word in word_set:
                suffixes = helper(i + L)
                for suf in suffixes:
                    if suf:
                        results.append(word + " " + suf)
                    else:
                        results.append(word)
        memo[i] = results
        return results

    return helper(0)


CASES = [
    {"s": "catsanddog", "wordDict": ["cat", "cats", "and", "sand", "dog"]},
    {"s": "pineapplepenapple", "wordDict": ["apple", "pen", "applepen", "pine", "pineapple"]},
    {"s": "catsandog", "wordDict": ["cats", "dog", "sand", "and", "cat"]},
    {"s": "a", "wordDict": ["a"]},
    {"s": "aaaa", "wordDict": ["a", "aa"]},
    {"s": "abc", "wordDict": ["a", "b", "c", "ab", "bc", "abc"]},
    {"s": "leetcoder", "wordDict": ["leet", "code", "coder", "leetcoder"]},
    {"s": "ab", "wordDict": ["a", "b"]},
]


if __name__ == '__main__':
    import json
    out = []
    for idx, case in enumerate(CASES):
        result = solve(case["s"], case["wordDict"])
        # Sort the result to make expected output canonical (order doesn't matter per problem)
        canonical = json.dumps(sorted(result), separators=(',', ':'), ensure_ascii=False)
        out.append({
            "id": idx,
            "input": {"s": case["s"], "wordDict": case["wordDict"]},
            "expected": canonical,
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
