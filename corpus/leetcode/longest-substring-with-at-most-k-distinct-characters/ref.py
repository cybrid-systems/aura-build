def solve(s: str, k: int) -> int:
    if k == 0 or not s:
        return 0
    freq = {}
    left = 0
    best = 0
    for right, ch in enumerate(s):
        freq[ch] = freq.get(ch, 0) + 1
        while len(freq) > k:
            lch = s[left]
            freq[lch] -= 1
            if freq[lch] == 0:
                del freq[lch]
            left += 1
        best = max(best, right - left + 1)
    return best


CASES = [
    {"s": "eceba", "k": 2},
    {"s": "aa", "k": 1},
    {"s": "", "k": 3},
    {"s": "abc", "k": 0},
    {"s": "a", "k": 1},
    {"s": "abaccc", "k": 2},
    {"s": "abcdefghijklmnopqrstuvwxyz", "k": 3},
    {"s": "aaaaaaaaaa", "k": 5},
]


if __name__ == '__main__':
    import json
    out = []
    for i, case in enumerate(CASES):
        s = case["s"]
        k = case["k"]
        result = solve(s, k)
        out.append({"id": i, "input": case, "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
