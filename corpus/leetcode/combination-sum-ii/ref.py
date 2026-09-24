def solve(candidates: list[int], target: int) -> list[list[int]]:
    candidates = sorted(candidates)
    result = []
    combo = []

    def backtrack(start: int, remaining: int):
        if remaining == 0:
            result.append(combo.copy())
            return
        if remaining < 0:
            return
        for i in range(start, len(candidates)):
            if i > start and candidates[i] == candidates[i - 1]:
                continue
            if candidates[i] > remaining:
                break
            combo.append(candidates[i])
            backtrack(i + 1, remaining - candidates[i])
            combo.pop()

    backtrack(0, target)
    return result


CASES = [
    {
        "candidates": [10, 1, 2, 7, 6, 1, 5],
        "target": 8,
    },
    {
        "candidates": [2, 5, 2, 1, 2],
        "target": 5,
    },
    {
        "candidates": [1, 1, 1, 1, 1],
        "target": 3,
    },
    {
        "candidates": [],
        "target": 1,
    },
    {
        "candidates": [1],
        "target": 1,
    },
    {
        "candidates": [1, 2, 3, 4, 5],
        "target": 9,
    },
    {
        "candidates": [3, 1, 3, 5, 1, 1],
        "target": 8,
    },
]


if __name__ == "__main__":
    import json

    output = []
    for i, case in enumerate(CASES):
        result = solve(case["candidates"], case["target"])
        normalized = json.dumps(result, separators=(",", ":"), ensure_ascii=False)
        output.append(
            {
                "id": i,
                "input": case,
                "expected": normalized,
            }
        )
    print(json.dumps(output, separators=(",", ":"), ensure_ascii=False))
