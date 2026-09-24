import sys
import json

def solve(meetings):
    if not meetings:
        return 0
    starts = sorted(s[0] for s in meetings)
    ends = sorted(s[1] for s in meetings)
    rooms = 0
    cur = 0
    i = j = 0
    n = len(meetings)
    while i < n:
        if starts[i] < ends[j]:
            cur += 1
            if cur > rooms:
                rooms = cur
            i += 1
        else:
            cur -= 1
            j += 1
    return rooms

CASES = [
    {"meetings": []},
    {"meetings": [(0, 30)]},
    {"meetings": [(0, 30), (5, 10), (15, 20)]},
    {"meetings": [(0, 10), (10, 20), (20, 30)]},
    {"meetings": [(1, 5), (2, 6), (4, 8)]},
    {"meetings": [(0, 5), (0, 5), (0, 5)]},
    {"meetings": [(0, 8), (1, 3), (3, 6), (5, 9), (7, 11)]},
    {"meetings": [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)]},
]

if __name__ == '__main__':
    results = []
    for idx, case in enumerate(CASES):
        result = solve(**case)
        results.append({
            "id": idx,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
