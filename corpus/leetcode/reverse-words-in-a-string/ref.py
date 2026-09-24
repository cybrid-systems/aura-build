def solve(s: str) -> str:
    words = s.split()
    return ' '.join(reversed(words))

CASES = [
    {"s": "the sky is blue"},
    {"s": "  hello world  "},
    {"s": "a   b   c"},
    {"s": "   "},
    {"s": ""},
    {"s": "single"},
    {"s": "  leading and trailing  "},
    {"s": "one  two\tthree"},
]

if __name__ == '__main__':
    import json
    out = []
    for i, c in enumerate(CASES):
        result = solve(c["s"])
        out.append({
            "id": i,
            "input": {"s": c["s"]},
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
