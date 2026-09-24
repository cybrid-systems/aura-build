def solve(nums: list[int]) -> list[int]:
    if not nums:
        return []
    n = len(nums)
    # Boyer-Moore majority vote for n/3
    c1 = c2 = None
    cnt1 = cnt2 = 0
    for x in nums:
        if c1 == x:
            cnt1 += 1
        elif c2 == x:
            cnt2 += 1
        elif cnt1 == 0:
            c1 = x
            cnt1 = 1
        elif cnt2 == 0:
            c2 = x
            cnt2 = 1
        else:
            cnt1 -= 1
            cnt2 -= 1
    # Verify counts
    cnt1 = cnt2 = 0
    for x in nums:
        if x == c1:
            cnt1 += 1
        elif x == c2:
            cnt2 += 1
    res = []
    threshold = n // 3
    if c1 is not None and cnt1 > threshold:
        res.append(c1)
    if c2 is not None and cnt2 > threshold:
        res.append(c2)
    return res


CASES = [
    {"nums": [3, 2, 3, 2, 1, 1, 1]},
    {"nums": [1, 2]},
    {"nums": [1]},
    {"nums": [1, 1, 1]},
    {"nums": [1, 2, 3, 4]},
    {"nums": [5, 5, 5, 5, 1, 2, 3]},
    {"nums": [2, 2, 2]},
    {"nums": []},
]


if __name__ == '__main__':
    import json
    out = []
    for i, c in enumerate(CASES):
        result = solve(c["nums"])
        out.append({
            "id": i,
            "input": c,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
