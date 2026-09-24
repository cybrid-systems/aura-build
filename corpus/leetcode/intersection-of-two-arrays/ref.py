def solve(a: list[int], b: list[int]) -> list[int]:
    set_a = set(a)
    set_b = set(b)
    intersection = set_a & set_b
    return list(intersection)

CASES = [
    {"a": [1, 2, 2, 3], "b": [2, 3, 4]},
    {"a": [1, 2, 3], "b": [4, 5, 6]},
    {"a": [], "b": [1, 2, 3]},
    {"a": [1, 1, 1], "b": [1, 2, 3]},
    {"a": [-1, -2, -3], "b": [-2, -3, -4]},
    {"a": [1, 2, 3, 4, 5], "b": [3, 4, 5, 6, 7]},
    {"a": [0, 0, 0], "b": [0]},
    {"a": [1, 2, 3], "b": []},
]

if __name__ == '__main__':
    import json
    results = []
    for i, case in enumerate(CASES):
        result = solve(case["a"], case["b"])
        if isinstance(result, list):
            result_sorted = sorted(result)
        else:
            result_sorted = result
        results.append({
            "id": i,
            "input": {"a": case["a"], "b": case["b"]},
            "expected": json.dumps(result_sorted, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
