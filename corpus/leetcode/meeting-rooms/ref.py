def solve(n, intervals):
    if n <= 1:
        return True
    s = sorted(intervals, key=lambda x: x[0])
    for i in range(n - 1):
        if s[i][1] > s[i + 1][0]:
            return False
    return True


CASES = [
    {"n": 0, "intervals": []},
    {"n": 1, "intervals": [[0, 5]]},
    {"n": 3, "intervals": [[0, 30], [5, 10], [15, 20]]},
    {"n": 2, "intervals": [[5, 10], [0, 5]]},
    {"n": 4, "intervals": [[1, 4], [4, 8], [8, 12], [12, 16]]},
    {"n": 3, "intervals": [[1, 5], [3, 7], [6, 10]]},
    {"n": 5, "intervals": [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5]]},
    {"n": 2, "intervals": [[0, 10], [10, 20]]},
]

if __name__ == '__main__':
    import json
    out = []
    for i, c in enumerate(CASES):
        result = solve(c["n"], c["intervals"])
        out.append({"id": i, "input": c, "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
