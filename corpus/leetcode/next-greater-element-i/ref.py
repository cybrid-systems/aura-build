import json

def solve(nums1, nums2):
    # Monotonic decreasing stack: values in stack are decreasing from bottom to top.
    # Scan nums2 left-to-right; for each num, pop while top < num, recording next-greater.
    nxt = {}
    stack = []
    for num in nums2:
        while stack and stack[-1] < num:
            nxt[stack.pop()] = num
        stack.append(num)
    # Remaining stack entries have no greater element to their right.
    return [nxt.get(x, -1) for x in nums1]


CASES = [
    {"nums1": [4, 1, 2], "nums2": [1, 3, 4, 2]},
    {"nums1": [2, 4], "nums2": [1, 2, 3, 4]},
    {"nums1": [], "nums2": [1, 2, 3]},
    {"nums1": [1, 2, 3], "nums2": []},
    {"nums1": [5], "nums2": [5]},
    {"nums1": [1, 1, 1], "nums2": [1, 2, 3]},
    {"nums1": [3, 2, 1], "nums2": [1, 2, 3, 4, 5]},
    {"nums1": [9, 7, 5, 3, 1], "nums2": [1, 3, 5, 7, 9]},
]


if __name__ == '__main__':
    out = []
    for i, c in enumerate(CASES):
        result = solve(c["nums1"], c["nums2"])
        out.append({
            "id": i,
            "input": {"nums1": c["nums1"], "nums2": c["nums2"]},
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
