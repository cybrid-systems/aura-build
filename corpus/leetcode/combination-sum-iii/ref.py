import json
from itertools import combinations

def solve(k, n):
    results = []
    # Use itertools.combinations for a clean, exhaustive solution
    # since the search space (1..9) is tiny.
    for combo in combinations(range(1, 10), k):
        if sum(combo) == n:
            results.append(list(combo))
    return results

CASES = [
    {"k": 3, "n": 7},
    {"k": 3, "n": 9},
    {"k": 4, "n": 1},
    {"k": 2, "n": 10},
    {"k": 9, "n": 45},
    {"k": 9, "n": 46},
    {"k": 2, "n": 17},
    {"k": 3, "n": 15},
]

def canonical(results):
    """Sort combinations and the list itself for deterministic output."""
    sorted_results = sorted([sorted(combo) for combo in results])
    return sorted_results

def render(results):
    """Convert results into the textual format described in the problem."""
    if not results:
        return ""
    sorted_results = sorted([sorted(combo) for combo in results])
    lines = [" ".join(str(x) for x in combo) for combo in sorted_results]
    return "\n".join(lines)

if __name__ == '__main__':
    out = []
    for i, case in enumerate(CASES):
        k = case["k"]
        n = case["n"]
        result = solve(k, n)
        canon = canonical(result)
        out.append({
            "id": i,
            "input": {"k": k, "n": n},
            "expected": json.dumps(canon, separators=(',', ':'), ensure_ascii=False),
            "output": render(result),
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
