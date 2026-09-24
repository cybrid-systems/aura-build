def solve(intervals, queries):
    import heapq

    # Sort intervals by left endpoint
    sorted_intervals = sorted(intervals, key=lambda x: x[0])

    # Sort queries while remembering original indices
    indexed_queries = sorted([(q, i) for i, q in enumerate(queries)])

    result = [-1] * len(queries)
    heap = []  # min-heap of (right_endpoint, left_endpoint)
    idx = 0
    n = len(sorted_intervals)

    for q, qi in indexed_queries:
        # Add all intervals whose left endpoint <= q
        while idx < n and sorted_intervals[idx][0] <= q:
            l, r = sorted_intervals[idx]
            heapq.heappush(heap, (r, l))
            idx += 1

        # Remove intervals whose right endpoint < q (they don't cover q)
        while heap and heap[0][0] < q:
            heapq.heappop(heap)

        if heap:
            r, l = heap[0]
            result[qi] = r - l + 1
        else:
            result[qi] = -1

    return result


CASES = [
    {
        "intervals": [[1, 4], [2, 8], [3, 6], [4, 8]],
        "queries": [3, 4, 5, 6, 7, 8],
    },
    {
        "intervals": [],
        "queries": [1, 2, 3],
    },
    {
        "intervals": [[1, 5]],
        "queries": [1, 2, 3, 4, 5, 6],
    },
    {
        "intervals": [[1, 4], [2, 4], [3, 4], [4, 4]],
        "queries": [4, 3, 2, 1, 5],
    },
    {
        "intervals": [[1, 10], [2, 3], [5, 5], [7, 9]],
        "queries": [2, 5, 7, 10, 11],
    },
    {
        "intervals": [[-5, -1], [0, 0], [-3, 3]],
        "queries": [-4, -2, 0, 1, -5, 4],
    },
    {
        "intervals": [[1, 2], [1, 2], [1, 2]],
        "queries": [1, 2, 3],
    },
    {
        "intervals": [[1, 100]],
        "queries": [50],
    },
]


if __name__ == "__main__":
    import json

    out = []
    for i, c in enumerate(CASES):
        result = solve(c["intervals"], c["queries"])
        out.append({
            "id": i,
            "input": {
                "intervals": c["intervals"],
                "queries": c["queries"],
            },
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
