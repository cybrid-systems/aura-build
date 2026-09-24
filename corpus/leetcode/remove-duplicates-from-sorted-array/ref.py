def solve(nums: list[int]) -> int:
    k = 0
    for x in nums:
        if k == 0 or x != nums[k - 1]:
            nums[k] = x
            k += 1
    return k


CASES = [
    {"nums": [1, 1, 2, 2, 3, 4, 4]},
    {"nums": []},
    {"nums": [1, 1, 1, 1, 1]},
    {"nums": [0]},
    {"nums": [-3, -3, -2, -1, -1, 0, 0, 0, 1, 2, 2]},
    {"nums": [1, 2, 3, 4, 5]},
    {"nums": [1, 2, 2, 3, 3, 3, 4, 5, 5]},
    {"nums": [0, 0, 0, 0, 0, 0]},
]


if __name__ == '__main__':
    import json
    out = []
    for i, c in enumerate(CASES):
        nums = list(c["nums"])
        k = solve(nums)
        first_k = nums[:k]
        record = {"id": i, "input": {"nums": c["nums"]}, "expected": {"k": k, "first_k": first_k}}
        out.append(record)
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
