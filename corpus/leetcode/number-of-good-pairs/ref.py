def solve(nums):
    freq = {}
    count = 0
    for n in nums:
        if n in freq:
            count += freq[n]
            freq[n] += 1
        else:
            freq[n] = 1
    return count


CASES = [
    {"nums": [1, 2, 3, 1, 1, 3]},
    {"nums": [1, 1, 1, 1]},
    {"nums": [1, 2, 3]},
    {"nums": [1]},
    {"nums": [0, 0, 0, 0, 0]},
    {"nums": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]},
    {"nums": [-1, -1, -1, 1, 1]},
    {"nums": [100, -100, 100, -100, 100, -100]},
]


if __name__ == '__main__':
    import json
    results = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        results.append({
            "id": i,
            "input": {"nums": case["nums"]},
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
