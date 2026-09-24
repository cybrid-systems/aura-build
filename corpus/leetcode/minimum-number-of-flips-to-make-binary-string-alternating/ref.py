def solve(s):
    n = len(s)
    if n <= 1:
        return 0
    ss = s + s
    # prefix[i] = mismatches in ss[0:i] against pattern starting with '0'
    pref0 = [0] * (2 * n + 1)
    pref1 = [0] * (2 * n + 1)
    for i in range(2 * n):
        c = ss[i]
        pref0[i + 1] = pref0[i] + (1 if c != ('0' if i % 2 == 0 else '1') else 0)
        pref1[i + 1] = pref1[i] + (1 if c != ('1' if i % 2 == 0 else '0') else 0)
    
    best = min(pref0[n], pref1[n])
    for i in range(1, n + 1):
        m0 = pref0[i + n] - pref0[i]
        m1 = pref1[i + n] - pref1[i]
        if m0 < best:
            best = m0
        if m1 < best:
            best = m1
    return best


CASES = [
    {"s": "1111"},
    {"s": "010"},
    {"s": "1110"},
    {"s": "010101"},
    {"s": "101010"},
    {"s": "0"},
    {"s": "1"},
    {"s": "00"},
    {"s": "01"},
    {"s": "10"},
    {"s": "0001"},
    {"s": "110100"},
]


if __name__ == '__main__':
    import json
    results = []
    for i, c in enumerate(CASES):
        r = solve(c["s"])
        results.append({"id": i, "input": c, "expected": json.dumps(r, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(results, ensure_ascii=False))
