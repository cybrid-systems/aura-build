def solve(nums: list[int], left: int, right: int) -> int:
    result = 0
    last_in_range = -1
    last_too_big = -1
    for i, v in enumerate(nums):
        if v > right:
            last_too_big = i
        if left <= v <= right:
            last_in_range = i
        result += last_in_range - last_too_big
    return result


CASES = [
    {"nums": [2, 1, 4, 3], "left": 2, "right": 3},
    {"nums": [2, 9, 2, 5, 6], "left": 2, "right": 8},
    {"nums": [1, 2, 3, 4], "left": 2, "right": 3},
    {"nums": [1, 4, 2, 3], "left": 3, "right": 3},
    {"nums": [0], "left": 0, "right": 0},
    {"nums": [-1, -2, -3], "left": -2, "right": -1},
    {"nums": [5, 5, 5, 5], "left": 5, "right": 5},
    {"nums": [10, 1, 2, 3, 4, 5], "left": 1, "right": 9},
]


if __name__ == "__main__":
    import json
    out = []
    for i, c in enumerate(CASES):
        res = solve(c["nums"], c["left"], c["right"])
        out.append({
            "id": i,
            "input": {"nums": c["nums"], "left": c["left"], "right": c["right"]},
            "expected": json.dumps(res, separators=(",", ":"), ensure_ascii=False),
        })
    print(json.dumps(out, separators=(",", ":"), ensure_ascii=False))
