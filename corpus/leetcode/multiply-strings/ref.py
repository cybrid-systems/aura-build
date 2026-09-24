def solve(a: str, b: str) -> str:
    # Edge cases: empty or "0"
    if not a or not b or a == "0" or b == "0":
        return "0"
    
    n, m = len(a), len(b)
    # Result can have at most n + m digits
    res = [0] * (n + m)
    
    # Long multiplication on reversed digit arrays
    for i in range(n - 1, -1, -1):
        ai = ord(a[i]) - 48  # digit value at position i in a
        for j in range(m - 1, -1, -1):
            bj = ord(b[j]) - 48  # digit value at position j in b
            # Positions in res correspond to (n-1-i) + (m-1-j)
            # i.e., res[(n-1-i) + (m-1-j)] and res[(n-1-i) + (m-1-j) + 1]
            p = (n - 1 - i) + (m - 1 - j)
            prod = ai * bj + res[p + 1]
            res[p + 1] = prod % 10
            res[p] += prod // 10
    
    # Convert to string, stripping leading zeros
    start = 0
    while start < len(res) - 1 and res[start] == 0:
        start += 1
    return "".join(chr(d + 48) for d in res[start:])


CASES = [
    {"a": "2", "b": "3"},
    {"a": "123", "b": "456"},
    {"a": "0", "b": "99"},
    {"a": "999", "b": "999"},
    {"a": "", "b": "5"},
    {"a": "0", "b": "0"},
    {"a": "1", "b": "1"},
    {"a": "9", "b": "9"},
    {"a": "100", "b": "100"},
    {"a": "12345", "b": "67890"},
    {"a": "99999999999999999999", "b": "99999999999999999999"},
    {"a": "123456789012345678901234567890", "b": "987654321098765432109876543210"},
]


if __name__ == '__main__':
    import json
    out = []
    for i, c in enumerate(CASES):
        result = solve(c["a"], c["b"])
        out.append({
            "id": i,
            "input": c,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
