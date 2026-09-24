import json

def solve(intervals):
    """Return the minimum number of intervals to remove so the remaining
    intervals are pairwise non-overlapping (strict overlap convention:
    intervals that only touch at endpoints do NOT overlap)."""
    if not intervals:
        return 0
    # Greedy interval scheduling: sort by end coordinate, keep the interval
    # with the earliest end time that is still compatible with the previously
    # kept interval. An interval [a,b] is kept iff its start is >= the last
    # kept interval's end (i.e., b of the previous is not strictly between
    # a and b of the current -- no interior intersection).
    sorted_intervals = sorted(intervals, key=lambda iv: iv[1])
    last_end = float('-inf')
    removed = 0
    for start, end in sorted_intervals:
        if start >= last_end:
            last_end = end
        else:
            removed += 1
    return removed


CASES = [
    # Example 1: endpoint-touching chains need 0 removals
    {"intervals": [[1, 2], [2, 3], [3, 4]]},
    # Example 2: four intervals where one must be removed
    {"intervals": [[1, 2], [1, 3], [2, 3], [3, 4]]},
    # Edge: empty input
    {"intervals": []},
    # Edge: single interval
    {"intervals": [[5, 10]]},
    # Edge: all overlap (each strictly contained in the next)
    {"intervals": [[1, 5], [2, 6], [3, 7]]},
    # Unsorted, all non-overlapping
    {"intervals": [[1, 2], [3, 4], [2, 3]]},
    # One huge interval swallows three small ones
    {"intervals": [[1, 100], [2, 3], [4, 5], [6, 7]]},
    # Tie-breaking on equal end points: keep earliest start
    {"intervals": [[1, 3], [2, 3], [3, 3], [4, 6]]},
]


if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        results.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
