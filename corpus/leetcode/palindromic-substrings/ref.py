def solve(s: str) -> int:
    n = len(s)
    seen = set()
    for center in range(n):
        # Odd-length palindromes
        l, r = center, center
        while l >= 0 and r < n and s[l] == s[r]:
            seen.add(s[l:r+1])
            l -= 1
            r += 1
        # Even-length palindromes
        l, r = center, center + 1
        while l >= 0 and r < n and s[l] == s[r]:
            seen.add(s[l:r+1])
            l -= 1
            r += 1
    return len(seen)


CASES = [
    {"s": "aba"},
    {"s": "aaaa"},
    {"s": "abc"},
    {"s": "a"},
    {"s": "ababa"},
    {"s": "abbaa"},
    {"s": "zxyxz"},
    {"s": "abcdefg"},
]


if __name__ == '__main__':
    import json
    out = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        out.append({"id": i, "input": case, "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(out, ensure_ascii=False))
