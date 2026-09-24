def solve(nums, firstLen, secondLen):
    n = len(nums)
    # prefix max of firstLen windows
    prefix_max = [0] * n
    s = sum(nums[:firstLen])
    prefix_max[firstLen - 1] = s
    for i in range(firstLen, n):
        s += nums[i] - nums[i - firstLen]
        prefix_max[i] = max(prefix_max[i - 1], s)

    # suffix max of secondLen windows
    suffix_max = [0] * n
    s = sum(nums[n - secondLen:])
    suffix_max[n - secondLen] = s
    for i in range(n - secondLen - 1, -1, -1):
        s += nums[i] - nums[i + secondLen]
        suffix_max[i] = max(suffix_max[i + 1], s)

    # order: firstLen before secondLen
    best = 0
    for i in range(firstLen - 1, n - secondLen):
        best = max(best, prefix_max[i] + suffix_max[i + 1])

    # swap and recompute
    prefix_max2 = [0] * n
    s = sum(nums[:secondLen])
    prefix_max2[secondLen - 1] = s
    for i in range(secondLen, n):
        s += nums[i] - nums[i - secondLen]
        prefix_max2[i] = max(prefix_max2[i - 1], s)

    suffix_max2 = [0] * n
    s = sum(nums[n - firstLen:])
    suffix_max2[n - firstLen] = s
    for i in range(n - firstLen - 1, -1, -1):
        s += nums[i] - nums[i + firstLen]
        suffix_max2[i] = max(suffix_max2[i + 1], s)

    for i in range(secondLen - 1, n - firstLen):
        best = max(best, prefix_max2[i] + suffix_max2[i + 1])

    return best


CASES = [
    {"nums": [0, 6, 5, 2, 2, 5, 1, 9, 4], "firstLen": 1, "secondLen": 2},
    {"nums": [3, 8, 1, 3, 2, 1, 4, 4], "firstLen": 2, "secondLen": 3},
    {"nums": [2, 1, 5, 6, 0, 9, 5, 0, 3, 8], "firstLen": 1, "secondLen": 1},
    {"nums": [1, 2, 3, 4, 5], "firstLen": 2, "secondLen": 3},
    {"nums": [5, 5, 5, 5, 5], "firstLen": 2, "secondLen": 2},
    {"nums": [1], "firstLen": 1, "secondLen": 1},
    {"nums": [0, 6, 5, 2, 2, 5, 1, 9, 4], "firstLen": 2, "secondLen": 3},
    {"nums": [3, 8, 1, 3, 2, 1, 4, 4], "firstLen": 3, "secondLen": 2},
]


if __name__ == '__main__':
    import json
    results = []
    for i, c in enumerate(CASES):
        out = solve(c["nums"], c["firstLen"], c["secondLen"])
        results.append({
            "id": i,
            "input": c,
            "expected": json.dumps(out, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
