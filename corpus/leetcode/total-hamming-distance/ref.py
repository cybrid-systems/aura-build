def solve(nums: list[int]) -> int:
    total = 0
    n = len(nums)
    if n < 2:
        return 0
    # Iterate over bit positions up to a reasonable max (e.g., 32 for typical inputs)
    # Python handles unbounded ints, but practical input fits in 32 bits
    for bit in range(32):
        count_ones = 0
        mask = 1 << bit
        for x in nums:
            if x & mask:
                count_ones += 1
        total += count_ones * (n - count_ones)
    return total


CASES = [
    {"nums": []},
    {"nums": [0]},
    {"nums": [0, 0]},
    {"nums": [1, 1]},
    {"nums": [4, 14, 2]},
    {"nums": [1, 2, 3]},
    {"nums": [5, 2, 7, 8]},
    {"nums": [0, 0, 0, 0, 0]},
    {"nums": [1, 3, 5, 7, 9, 11, 13, 15]},
    {"nums": [255, 255, 255, 255]},
]


if __name__ == '__main__':
    import json
    out = []
    for idx, case in enumerate(CASES):
        args = case["nums"]
        result = solve(args)
        out.append({"id": idx, "input": {"nums": args}, "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
