def solve(s):
    n = len(s)
    if n == 0:
        return [[]]
    res = []
    def is_pal(i, j):
        while i < j:
            if s[i] != s[j]:
                return False
            i += 1
            j -= 1
        return True
    def backtrack(start, path):
        if start == n:
            res.append(path[:])
            return
        for end in range(start, n):
            if is_pal(start, end):
                path.append(s[start:end+1])
                backtrack(end+1, path)
                path.pop()
    backtrack(0, [])
    return res

CASES = [
    {"s": "aab"},
    {"s": "a"},
    {"s": "aba"},
    {"s": "abba"},
    {"s": "aaaa"},
    {"s": "abc"},
    {"s": "aabaa"},
    {"s": "ab"},
]

if __name__ == '__main__':
    import json
    out = []
    for i, c in enumerate(CASES):
        result = solve(**c)
        out.append({"id": i, "input": c, "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
