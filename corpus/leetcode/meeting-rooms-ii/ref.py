import sys
import json

def min_meeting_rooms(intervals):
    if not intervals:
        return 0
    n = len(intervals)
    starts = [0] * n
    ends = [0] * n
    for i, (s, e) in enumerate(intervals):
        starts[i] = s
        ends[i] = e
    starts.sort()
    ends.sort()
    rooms = 0
    end_ptr = 0
    for i in range(n):
        if starts[i] < ends[end_ptr]:
            rooms += 1
        else:
            end_ptr += 1
    return rooms

def solve(intervals):
    return min_meeting_rooms(intervals)

CASES = [
    {"intervals": [[0, 30], [5, 10], [15, 20]]},
    {"intervals": [[7, 10], [2, 4]]},
    {"intervals": [[1, 4], [4, 6], [4, 7]]},
    {"intervals": []},
    {"intervals": [[1, 5]]},
    {"intervals": [[1, 5], [2, 6], [3, 7], [4, 8]]},
    {"intervals": [[1, 4], [2, 3]]},
    {"intervals": [[0, 1], [1, 2], [2, 3], [3, 4]]},
]

if __name__ == '__main__':
    results = []
    for idx, case in enumerate(CASES):
        result = solve(**case)
        results.append({
            "id": idx,
            "input": {k: v for k, v in case.items()},
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
