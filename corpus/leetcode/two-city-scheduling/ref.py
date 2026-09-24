import sys
import json

def solve(n, cost):
    # Greedy: sort by savings of choosing A over B (i.e., cost_b - cost_a, ascending).
    # The n people with the smallest (cost_b - cost_a) -> highest savings if sent to A -> send to A.
    # Others go to B.
    # Tie-break is irrelevant because sums will be the same.
    # Index = list of (saving = cost[i][1] - cost[i][0], i)
    indexed = sorted(range(len(cost)), key=lambda i: cost[i][1] - cost[i][0])
    total = 0
    for k, i in enumerate(indexed):
        if k < n:
            total += cost[i][0]  # to A
        else:
            total += cost[i][1]  # to B
    return total

CASES = [
    # Example 1
    {"n": 2, "cost": [[10, 20], [30, 200], [400, 50], [30, 20]]},
    # n=1, minimal
    {"n": 1, "cost": [[10, 20], [30, 200]]},
    # all equal costs -> any split, sum = n*(a+b)
    {"n": 2, "cost": [[50, 50], [50, 50], [50, 50], [50, 50]]},
    # extreme: everyone strongly prefers B, but still need n in A
    {"n": 2, "cost": [[1000, 0], [1000, 0], [1000, 0], [1000, 0]]},
    # extreme: everyone strongly prefers A
    {"n": 2, "cost": [[0, 1000], [0, 1000], [0, 1000], [0, 1000]]},
    # mixed
    {"n": 3, "cost": [[1, 2], [3, 4], [5, 6], [7, 8], [9, 10], [11, 12]]},
    # zeros allowed
    {"n": 2, "cost": [[0, 0], [0, 0], [0, 0], [0, 0]]},
    # tie scenario
    {"n": 2, "cost": [[10, 10], [20, 20], [30, 30], [40, 40]]},
]

if __name__ == '__main__':
    out = []
    for idx, case in enumerate(CASES):
        result = solve(case["n"], case["cost"])
        out.append({
            "id": idx,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
