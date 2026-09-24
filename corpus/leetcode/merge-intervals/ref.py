from typing import List, Tuple

def solve(intervals: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    if not intervals:
        return []
    sorted_intervals = sorted(intervals, key=lambda x: (x[0], x[1]))
    merged: List[Tuple[int, int]] = [sorted_intervals[0]]
    for start, end in sorted_intervals[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))
    return merged


CASES = [
    {"id": 0, "input": [(1, 3), (2, 6), (8, 10), (15, 18)]},
    {"id": 1, "input": [(1, 4), (4, 5)]},
    {"id": 2, "input": [(1, 4), (0, 4)]},
    {"id": 3, "input": []},
    {"id": 4, "input": [(1, 4), (2, 3)]},
    {"id": 5, "input": [(1, 4)]},
    {"id": 6, "input": [(4, 4), (1, 4), (2, 6), (0, 0), (8, 10), (15, 18)]},
    {"id": 7, "input": [(3, 5), (-2, 1), (1, 4), (10, 12), (12, 15)]},
]


if __name__ == '__main__':
    import json
    out = []
    for case in CASES:
        result = solve(list(case["input"]))
        out.append({
            "id": case["id"],
            "input": case["input"],
            "expected": json.dumps([list(p) for p in result], separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
