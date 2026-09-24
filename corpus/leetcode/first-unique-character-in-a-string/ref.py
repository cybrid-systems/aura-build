def solve(s):
    counts = [0] * 26
    for ch in s:
        counts[ord(ch) - 97] += 1
    for i, ch in enumerate(s):
        if counts[ord(ch) - 97] == 1:
            return i
    return -1

CASES = [
    {"s": "loveleetcode"},
    {"s": "aabbcc"},
    {"s": "z"},
    {"s": "abc"},
    {"s": "aabbc"},
    {"s": "abacabad"},
    {"s": "aaaaa"},
    {"s": "abcdefghijklmnopqrstuvwxyz"},
]

if __name__ == '__main__':
    import json
    out = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        out.append({"id": i, "input": case, "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
