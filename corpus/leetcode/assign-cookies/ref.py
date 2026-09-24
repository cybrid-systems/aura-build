def solve(greed: list[int], size: list[int]) -> int:
    greed_sorted = sorted(greed)
    size_sorted = sorted(size)
    i = j = 0
    count = 0
    while i < len(greed_sorted) and j < len(size_sorted):
        if size_sorted[j] >= greed_sorted[i]:
            count += 1
            i += 1
            j += 1
        else:
            j += 1
    return count


CASES = [
    {"greed": [1, 2, 3], "size": [1, 1]},
    {"greed": [1, 2], "size": [1, 2, 3]},
    {"greed": [1, 2, 3], "size": [3]},
    {"greed": [10, 9, 8, 7], "size": [5, 6, 7, 8]},
    {"greed": [1, 1, 1, 1], "size": [1, 1, 1, 1]},
    {"greed": [0, 0, 0], "size": [0, 0, 0]},
    {"greed": [5], "size": [1, 2, 3, 4]},
    {"greed": [1, 5, 7], "size": [2, 3, 6]},
]


if __name__ == '__main__':
    import json
    results = []
    for idx, case in enumerate(CASES):
        result = solve(case["greed"], case["size"])
        results.append({
            "id": idx,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
