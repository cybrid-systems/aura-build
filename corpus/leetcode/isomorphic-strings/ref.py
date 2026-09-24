def solve(s: str, t: str) -> bool:
    if len(s) != len(t):
        return False
    s_to_t = {}
    t_to_s = {}
    for a, b in zip(s, t):
        if a in s_to_t:
            if s_to_t[a] != b:
                return False
        else:
            s_to_t[a] = b
        if b in t_to_s:
            if t_to_s[b] != a:
                return False
        else:
            t_to_s[b] = a
    return True


CASES = [
    {"s": "egg", "t": "add"},
    {"s": "foo", "t": "bar"},
    {"s": "paper", "t": "title"},
    {"s": "ab", "t": "aa"},
    {"s": "", "t": ""},
    {"s": "a", "t": "a"},
    {"s": "abc", "t": "abcd"},
    {"s": "badc", "t": "baba"},
]


if __name__ == '__main__':
    import json
    results = []
    for i, case in enumerate(CASES):
        out = solve(**case)
        results.append({"id": i, "input": case, "expected": json.dumps(out, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
