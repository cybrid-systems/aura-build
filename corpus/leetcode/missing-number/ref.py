def solve(nums: list[int]) -> int:
    n = len(nums)
    expected = n * (n + 1) // 2
    return expected - sum(nums)


CASES = [
    {"nums": [3, 0, 1]},
    {"nums": [0, 1, 2, 3, 4, 5, 6, 7, 9]},
    {"nums": [0]},
    {"nums": [1]},
    {"nums": [1, 0]},
    {"nums": [0, 1, 3, 4, 5]},
    {"nums": list(range(1, 100))},
    {"nums": list(range(0, 50)) + list(range(51, 100))},
]


if __name__ == "__main__":
    import json
    out = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        out.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(",", ":"), ensure_ascii=False)
        })
    print(json.dumps(out, separators=(",", ":"), ensure_ascii=False))
