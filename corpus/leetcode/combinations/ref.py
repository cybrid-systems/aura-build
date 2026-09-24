import os
import json


def solve(n, k):
    if k > n or k < 0:
        return []
    result = []
    combo = []

    def backtrack(start):
        if len(combo) == k:
            result.append(combo.copy())
            return
        # Pruning: not enough remaining numbers
        remaining = n - start + 1
        needed = k - len(combo)
        if remaining < needed:
            return
        for i in range(start, n + 1):
            combo.append(i)
            backtrack(i + 1)
            combo.pop()

    backtrack(1)
    return result


def format_combo(combo):
    return "[" + " ".join(str(x) for x in combo) + "]"


CASES = [
    {"n": 4, "k": 2},
    {"n": 1, "k": 1},
    {"n": 5, "k": 3},
    {"n": 3, "k": 1},
    {"n": 6, "k": 4},
    {"n": 5, "k": 5},
    {"n": 5, "k": 6},
    {"n": 2, "k": 2},
]


if __name__ == "__main__":
    outputs = []
    for idx, case in enumerate(CASES):
        combos = solve(case["n"], case["k"])
        expected = ",".join(format_combo(c) for c in combos)
        outputs.append({
            "id": idx,
            "input": {"n": case["n"], "k": case["k"]},
            "expected": expected,
        })
    print(json.dumps(outputs, separators=(",", ":"), ensure_ascii=False))
