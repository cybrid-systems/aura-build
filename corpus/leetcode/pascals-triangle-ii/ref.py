def solve(k):
    row = [1]
    for i in range(1, k + 1):
        # Update in-place from right to left
        for j in range(i - 1, 0, -1):
            row[j] += row[j - 1]
        row.append(1)
    return row


CASES = [
    {"k": 0},
    {"k": 1},
    {"k": 2},
    {"k": 3},
    {"k": 4},
    {"k": 5},
    {"k": 10},
    {"k": 30},
]


if __name__ == '__main__':
    import json
    out = []
    for idx, case in enumerate(CASES):
        inp = {"k": case["k"]}
        result = solve(case["k"])
        expected = " ".join(str(x) for x in result)
        out.append({"id": idx, "input": inp, "expected": expected})
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
