def solve(s1: str, s2: str) -> bool:
    n, m = len(s1), len(s2)
    if n > m:
        return False
    count = [0] * 26
    base = ord('a')
    for c in s1:
        count[ord(c) - base] += 1
    window = [0] * 26
    for i in range(n):
        window[ord(s2[i]) - base] += 1
    if window == count:
        return True
    for i in range(n, m):
        window[ord(s2[i]) - base] += 1
        window[ord(s2[i - n]) - base] -= 1
        if window == count:
            return True
    return False


CASES = [
    {"s1": "abc", "s2": "abcbacab"},
    {"s1": "abc", "s2": "cab"},
    {"s1": "abcd", "s2": "dabc"},
    {"s1": "hello", "s2": "oooll"},
    {"s1": "a", "s2": "a"},
    {"s1": "a", "s2": "b"},
    {"s1": "ab", "s2": "ba"},
    {"s1": "abcd", "s2": "abcdefgh"},
]


if __name__ == '__main__':
    import json
    out = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        out.append({"id": i, "input": case, "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
