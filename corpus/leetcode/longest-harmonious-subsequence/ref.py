import json
from collections import Counter


def solve(values: list) -> int:
    if not values:
        return 0
    counts = Counter(values)
    best = 0
    for v in counts:
        if (v + 1) in counts:
            length = counts[v] + counts[v + 1]
            if length > best:
                best = length
    return best


CASES = [
    {"values": [1, 3, 2, 4, 3]},
    {"values": [1, 1, 1, 1]},
    {"values": []},
    {"values": [5, 6]},
    {"values": [1, 2, 3, 4, 5, 6]},
    {"values": [2, 2, 2, 3, 3, 4, 4, 4, 4]},
    {"values": [1, 2, 2, 3, 3, 3, 4]},
    {"values": [1, 3, 5, 7, 9]},
    {"values": [1, 2, 1, 3, 2, 4, 3, 5]},
]


if __name__ == "__main__":
    out = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        out.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(",", ":"), ensure_ascii=False),
        })
    print(json.dumps(out, separators=(",", ":"), ensure_ascii=False))
