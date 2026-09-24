def solve(x: int) -> int:
    if x < 2:
        return x
    left, right = 1, x // 2 + 1
    while left <= right:
        mid = left + (right - left) // 2
        if mid <= x // mid:
            left = mid + 1
        else:
            right = mid - 1
    return right


CASES = [
    {"x": 0},
    {"x": 1},
    {"x": 4},
    {"x": 8},
    {"x": 9},
    {"x": 15},
    {"x": 16},
    {"x": 2147395599},
]


if __name__ == "__main__":
    import json
    results = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        input_part = {k: v for k, v in case.items()}
        results.append({
            "id": i,
            "input": input_part,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
