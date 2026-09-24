def solve(s: str) -> str:
    seen = set()
    for ch in s:
        if ch in seen:
            return ch
        seen.add(ch)
    # Should never reach here due to problem guarantee
    return ""

CASES = [
    {"s": "abccba"},
    {"s": "abcdd"},
    {"s": "abcdefghijklmnopqrstuvwxyzops"},
    {"s": "a"},
    {"s": "aa"},
    {"s": "zxyxz"},
    {"s": "mnbvcxzpoiuytrewqasdfghjklmnb"},
    {"s": "abcdefghijklmnopqrstuvwxyza"},
]

if __name__ == '__main__':
    import json
    out = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        out.append({"id": i, "input": case, "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(out, ensure_ascii=False))
