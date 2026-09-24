def solve(s: str) -> str:
    if not s:
        return ""
    freq = {}
    for ch in s:
        freq[ch] = freq.get(ch, 0) + 1
    chars = sorted(freq.keys(), key=lambda c: -freq[c])
    result = []
    for ch in chars:
        result.append(ch * freq[ch])
    return "".join(result)


CASES = [
    {"s": "tree"},
    {"s": "Aabb"},
    {"s": "a"},
    {"s": ""},
    {"s": "aaabbb"},
    {"s": "Mississippi"},
    {"s": "abc"},
    {"s": "!!!??hello"},
]

if __name__ == '__main__':
    import json
    out = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        out.append({"id": i, "input": case, "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(out, ensure_ascii=False))
