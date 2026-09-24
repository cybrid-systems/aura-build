def solve(nums: list[int], k: int) -> bool:
    last_index = {}
    for i, n in enumerate(nums):
        if n in last_index and i - last_index[n] <= k:
            return True
        last_index[n] = i
    return False


CASES = [
    {"nums": [1, 2, 3, 1], "k": 3},
    {"nums": [1, 0, 1, 1], "k": 1},
    {"nums": [1, 2, 3, 1, 2, 3], "k": 2},
    {"nums": [], "k": 0},
    {"nums": [1], "k": 1},
    {"nums": [1, 1], "k": 0},
    {"nums": [1, 2, 3, 4, 5, 1], "k": 5},
    {"nums": [1, 2, 3, 4, 5, 1], "k": 4},
]


if __name__ == '__main__':
    import json
    results = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        results.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
