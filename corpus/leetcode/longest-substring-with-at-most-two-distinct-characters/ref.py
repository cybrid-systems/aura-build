def solve(s: str) -> int:
    if not s:
        return 0
    left = 0
    counts = {}
    best = 0
    for right, ch in enumerate(s):
        counts[ch] = counts.get(ch, 0) + 1
        while len(counts) > 2:
            lch = s[left]
            counts[lch] -= 1
            if counts[lch] == 0:
                del counts[lch]
            left += 1
        best = max(best, right - left + 1)
    return best


CASES = [
    {"s": "eceba"},
    {"s": "ccaabbb"},
    {"s": "a"},
    {"s": "abcd"},
    {"s": "aaaa"},
    {"s": "ababab"},
    {"s": "abcabcabc"},
    {"s": "aabbaa"},
]


if __name__ == '__main__':
    import json
    out = []
    for i, c in enumerate(CASES):
        result = solve(**c)
        out.append({
            "id": i,
            "input": c,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
