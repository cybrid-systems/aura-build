def solve(head: list[int], k: int) -> list[int]:
    n = len(head)
    if n == 0:
        return []
    k = k % n
    if k == 0:
        return list(head)
    # Rotate right by k: last k elements move to front
    return head[n - k:] + head[:n - k]


CASES = [
    {"head": [1, 2, 3, 4, 5], "k": 2},
    {"head": [], "k": 10},
    {"head": [1], "k": 100},
    {"head": [1, 2, 3], "k": 0},
    {"head": [1, 2, 3, 4, 5], "k": 5},
    {"head": [1, 2, 3, 4, 5], "k": 7},
    {"head": [10, 20, 30, 40], "k": 1},
    {"head": [5, 5, 5, 5], "k": 2},
]


if __name__ == '__main__':
    import json
    out = []
    for i, c in enumerate(CASES):
        result = solve(c["head"], c["k"])
        out.append({"id": i, "input": c, "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
