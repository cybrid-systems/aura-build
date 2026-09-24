def solve(n):
    if n < 1:
        return ""
    s = "1"
    for _ in range(n - 1):
        result = []
        i = 0
        L = len(s)
        while i < L:
            j = i
            while j < L and s[j] == s[i]:
                j += 1
            result.append(str(j - i))
            result.append(s[i])
            i = j
        s = "".join(result)
    return s

CASES = [
    {"n": 1},
    {"n": 2},
    {"n": 3},
    {"n": 4},
    {"n": 5},
    {"n": 6},
    {"n": 7},
    {"n": 10},
    {"n": 15},
    {"n": 20},
    {"n": 25},
    {"n": 30},
    {"n": 8},
    {"n": 9},
    {"n": 11},
]

if __name__ == '__main__':
    import json
    out = []
    for idx, c in enumerate(CASES):
        result = solve(**c)
        out.append({"id": idx, "input": c, "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
