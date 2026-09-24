def solve(nums):
    if not nums:
        return 0
    s = set(nums)
    longest = 0
    for x in s:
        if x - 1 not in s:
            length = 1
            cur = x
            while cur + 1 in s:
                cur += 1
                length += 1
            if length > longest:
                longest = length
    return longest


CASES = [
    {"nums": []},
    {"nums": [100, 4, 200, 1, 3, 2]},
    {"nums": [0, 3, 7, 2, 5, 8, 4, 6, 0, 1]},
    {"nums": [1, 2, 0, 1]},
    {"nums": [5, 5, 5]},
    {"nums": [-2, -1, 0, 1, 2, 3]},
    {"nums": [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]},
    {"nums": [10, 20, 30, 40]},
]


if __name__ == '__main__':
    import json
    out = []
    for i, c in enumerate(CASES):
        result = solve(**c)
        out.append({"id": i, "input": c, "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
