from collections import Counter

def solve(s: str) -> bool:
    if not s:
        return True
    counts = Counter(s)
    freq = set(counts.values())
    return len(freq) == 1

CASES = [
    {"s": "ababab"},
    {"s": "aaaaabbbbb"},
    {"s": "abc"},
    {"s": "aabbcc"},
    {"s": "aabbccc"},
    {"s": "aaaa"},
    {"s": ""},
    {"s": "a b c a b c"},
]

if __name__ == '__main__':
    import json
    out = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        out.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
