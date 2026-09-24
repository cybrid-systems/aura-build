def solve(arr):
    n = len(arr)
    if n < 2:
        return False
    total = sum(arr)
    if total % 2 != 0:
        return False
    target = total // 2
    # bitset DP: bit i set means sum i is achievable
    reachable = 1  # only sum 0 initially
    for x in arr:
        if x > target:
            return False
        reachable |= reachable << x
        # Optional mask to keep only bits up to target for speed
        reachable &= (1 << (target + 1)) - 1
    return (reachable >> target) & 1 == 1


CASES = [
    {"arr": [1, 5, 11, 5]},
    {"arr": [1, 2, 3, 4, 5, 6, 7]},
    {"arr": [1, 2, 3]},
    {"arr": []},
    {"arr": [0]},
    {"arr": [0, 0]},
    {"arr": [100, 100, 100, 100]},
    {"arr": [3, 3, 3, 3, 3, 3]},
]


if __name__ == '__main__':
    import json
    results = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        results.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
