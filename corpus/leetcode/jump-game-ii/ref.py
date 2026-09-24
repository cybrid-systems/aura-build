def solve(nums: list[int]) -> int:
    if len(nums) <= 1:
        return 0
    jumps = 0
    current_end = 0
    farthest = 0
    for i in range(len(nums) - 1):
        farthest = max(farthest, i + nums[i])
        if i == current_end:
            jumps += 1
            current_end = farthest
    return jumps


CASES = [
    {"nums": [2, 3, 1, 1, 4]},
    {"nums": [2, 3, 0, 1, 4]},
    {"nums": [1, 2, 3]},
    {"nums": [1, 1, 1, 1]},
    {"nums": [5, 4, 3, 2, 1, 1, 1, 1]},
    {"nums": [1, 2, 0, 1]},
    {"nums": [2, 0]},
    {"nums": [1] + [0] * 9 + [1]},
]


if __name__ == '__main__':
    import json
    out = []
    for idx, c in enumerate(CASES):
        result = solve(**c)
        inp = {"nums": c["nums"]}
        out.append({
            "id": idx,
            "input": inp,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(out, ensure_ascii=False))
