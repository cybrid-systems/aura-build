import json
from typing import List


def solve(intervals: List[List[int]], newInterval: List[int]) -> List[List[int]]:
    result = []
    i = 0
    n = len(intervals)
    ns, ne = newInterval[0], newInterval[1]

    # Add intervals before newInterval
    while i < n and intervals[i][1] < ns:
        result.append(intervals[i])
        i += 1

    # Merge overlapping intervals with newInterval
    while i < n and intervals[i][0] <= ne:
        ns = min(ns, intervals[i][0])
        ne = max(ne, intervals[i][1])
        i += 1
    result.append([ns, ne])

    # Add remaining intervals
    while i < n:
        result.append(intervals[i])
        i += 1

    return result


CASES = [
    {"intervals": [[1, 3], [6, 9]], "newInterval": [2, 5]},
    {"intervals": [[1, 2], [3, 5], [6, 7], [8, 10], [12, 16]], "newInterval": [4, 8]},
    {"intervals": [], "newInterval": [5, 7]},
    {"intervals": [], "newInterval": [1, 1]},
    {"intervals": [[1, 5]], "newInterval": [2, 3]},
    {"intervals": [[1, 5]], "newInterval": [5, 7]},
    {"intervals": [[1, 5]], "newInterval": [6, 8]},
    {"intervals": [[1, 2], [3, 4], [5, 6]], "newInterval": [10, 12]},
]


if __name__ == '__main__':
    out = []
    for idx, case in enumerate(CASES):
        result = solve(case["intervals"], case["newInterval"])
        out.append({
            "id": idx,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
