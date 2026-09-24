def solve(s: str, p: str) -> list[int]:
    if len(p) > len(s):
        return []
    need = {}
    for c in p:
        need[c] = need.get(c, 0) + 1
    window = {}
    missing = len(need)
    res = []
    pn = len(p)
    for i, c in enumerate(s):
        if c in need:
            window[c] = window.get(c, 0) + 1
            if window[c] == need[c]:
                missing -= 1
        if i >= pn:
            out = s[i - pn]
            if out in need:
                if window[out] == need[out]:
                    missing += 1
                window[out] -= 1
        if missing == 0:
            res.append(i - pn + 1)
    return res


CASES = [
    {"s": "cbaebabacd", "p": "abc"},
    {"s": "abab", "p": "ab"},
    {"s": "aaaaa", "p": "aa"},
    {"s": "abcd", "p": "efgh"},
    {"s": "abdc", "p": "abcd"},
    {"s": "a", "p": "a"},
    {"s": "a", "p": "b"},
    {"s": "abcabcabc", "p": "abc"},
]


if __name__ == '__main__':
    import json
    out = []
    for i, c in enumerate(CASES):
        r = solve(**c)
        out.append({"id": i, "input": c, "expected": json.dumps(r, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
