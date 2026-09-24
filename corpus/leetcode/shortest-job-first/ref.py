def solve(t: list[int]) -> int:
    t = sorted(t)
    total = 0
    running = 0
    for d in t:
        total += running
        running += d
    return total


CASES = [
    {"t": [4, 1, 3, 2]},
    {"t": [1]},
    {"t": [1, 1, 1, 1]},
    {"t": [10, 1, 9, 2, 8, 3, 7, 4, 6, 5]},
    {"t": [10000] * 200000},
    {"t": list(range(1, 11))},
    {"t": [5, 4, 3, 2, 1]},
    {"t": [2, 7, 4, 1, 9, 3]},
]


if __name__ == "__main__":
    import json
    out = []
    for i, c in enumerate(CASES):
        result = solve(**c)
        out.append({
            "id": i,
            "input": c,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
