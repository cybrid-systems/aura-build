from itertools import permutations

def solve(nums: list[int]) -> list[list[int]]:
    return [list(p) for p in permutations(nums)]

CASES = [
    {"nums": [1, 2, 3]},
    {"nums": [0, 1]},
    {"nums": [1]},
    {"nums": [5, 4, 3, 2, 1]},
    {"nums": [7]},
    {"nums": [-1, 0, 1]},
    {"nums": [10, 20, 30, 40]},
    {"nums": [2, 1]},
]

if __name__ == '__main__':
    import json
    results = []
    for i, case in enumerate(CASES):
        nums = case["nums"]
        perms = solve(nums)
        # canonical: sorted list of permutations (as tuples for stable JSON)
        canonical = sorted([tuple(p) for p in perms])
        canonical_str = json.dumps(canonical, separators=(',', ':'), ensure_ascii=False)
        results.append({"id": i, "input": case, "expected": canonical_str})
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
