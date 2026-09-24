import sys, json

def solve(N, a):
    if N == 0:
        return 0
    # Greedy: pick position 1, skip next, pick, skip, ...
    # Equivalent to ceil(N/2)
    count = 0
    i = 0
    last_picked = -2  # sentinel so first position can always be picked
    while i < N:
        if i - last_picked > 1:
            count += 1
            last_picked = i
        i += 1
    return count

CASES = [
    {"N": 5, "a": [10, 20, 30, 40, 50]},
    {"N": 4, "a": [1, 2, 3, 4]},
    {"N": 1, "a": [100]},
    {"N": 2, "a": [1, 2]},
    {"N": 3, "a": [1, 2, 3]},
    {"N": 6, "a": [-5, 0, 5, 10, 15, 20]},
    {"N": 7, "a": [1, 2, 3, 4, 5, 6, 7]},
    {"N": 10, "a": list(range(10))},
]

if __name__ == '__main__':
    out = []
    for i, c in enumerate(CASES):
        result = solve(c["N"], c["a"])
        expected = (c["N"] + 1) // 2  # ceil(N/2)
        out.append({
            "id": i,
            "input": {"N": c["N"], "a": c["a"]},
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
        # sanity: result should match ceil(N/2) for this variant
        assert result == expected, f"Mismatch on case {i}: {result} vs {expected}"
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
