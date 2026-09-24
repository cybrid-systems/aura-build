def solve(a, b):
    """Compute Levenshtein edit distance between strings a and b."""
    if len(a) < len(b):
        a, b = b, a
    n, m = len(a), len(b)
    if m == 0:
        return n
    # Use two rows: prev and curr
    prev = list(range(m + 1))
    curr = [0] * (m + 1)
    for i in range(1, n + 1):
        curr[0] = i
        ai = a[i - 1]
        for j in range(1, m + 1):
            if ai == b[j - 1]:
                curr[j] = prev[j - 1]
            else:
                # min of replace, delete, insert
                curr[j] = 1 + min(prev[j - 1], prev[j], curr[j - 1])
        prev, curr = curr, prev
    return prev[m]


CASES = [
    {"a": "kitten", "b": "sitting"},
    {"a": "abc", "b": "abc"},
    {"a": "", "b": "a"},
    {"a": "a", "b": ""},
    {"a": "", "b": ""},
    {"a": "sunday", "b": "saturday"},
    {"a": "horse", "b": "ros"},
    {"a": "intention", "b": "execution"},
]

if __name__ == '__main__':
    import json
    out = []
    for i, case in enumerate(CASES):
        result = solve(case["a"], case["b"])
        out.append({
            "id": i,
            "input": {"a": case["a"], "b": case["b"]},
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
