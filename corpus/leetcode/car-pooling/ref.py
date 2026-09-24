import json

def solve(n, capacity, trips):
    events = []
    for start, end, passengers in trips:
        events.append((start, 0, passengers))   # pickup: apply after
        events.append((end, 1, passengers))     # dropoff: apply before
    events.sort()
    current = 0
    for pos, kind, p in events:
        if kind == 1:  # dropoff first
            current -= p
        else:  # pickup
            current += p
            if current > capacity:
                return "NO"
    return "YES"

CASES = [
    {
        "n": 3,
        "capacity": 4,
        "trips": [[1, 5, 2], [2, 4, 3], [5, 9, 3]],
    },
    {
        "n": 2,
        "capacity": 2,
        "trips": [[1, 3, 2], [3, 5, 2]],
    },
    {
        "n": 2,
        "capacity": 3,
        "trips": [[1, 5, 2], [2, 6, 3]],
    },
    {
        "n": 1,
        "capacity": 1,
        "trips": [[0, 1000000000, 1]],
    },
    {
        "n": 3,
        "capacity": 5,
        "trips": [[1, 4, 3], [4, 7, 3], [2, 5, 2]],
    },
    {
        "n": 2,
        "capacity": 5,
        "trips": [[2, 5, 3], [5, 9, 3]],
    },
    {
        "n": 3,
        "capacity": 3,
        "trips": [[1, 3, 2], [3, 5, 2], [2, 4, 3]],
    },
    {
        "n": 1,
        "capacity": 1,
        "trips": [[5, 10, 1]],
    },
]

if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        result = solve(case["n"], case["capacity"], case["trips"])
        results.append({
            "id": i,
            "input": {
                "n": case["n"],
                "capacity": case["capacity"],
                "trips": case["trips"],
            },
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
