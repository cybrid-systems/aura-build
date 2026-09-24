def solve(numbers: list[int], target: int) -> list[int]:
    left, right = 0, len(numbers) - 1
    while left < right:
        s = numbers[left] + numbers[right]
        if s == target:
            return [left + 1, right + 1]
        if s < target:
            left += 1
        else:
            right -= 1
    return []


CASES = [
    {"numbers": [2, 7, 11, 15], "target": 9},
    {"numbers": [2, 3, 4], "target": 6},
    {"numbers": [-1, 0], "target": -1},
    {"numbers": [1, 2, 3, 4, 5, 6, 7, 8, 9], "target": 17},
    {"numbers": [-5, -3, -1, 2, 4, 6], "target": 1},
    {"numbers": [0, 0, 1, 2, 3], "target": 0},
    {"numbers": [1, 3, 4, 5, 7, 11], "target": 9},
    {"numbers": [-100, -50, -10, 10, 50, 100], "target": 0},
]


if __name__ == '__main__':
    import json
    out = []
    for i, case in enumerate(CASES):
        result = solve(case["numbers"], case["target"])
        out.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
