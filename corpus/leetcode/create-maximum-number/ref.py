def solve(nums1, nums2, k):
    def max_subseq(nums, t):
        # Greedy: pick t digits while preserving order, using a stack (monotonic decreasing).
        stack = []
        drop = len(nums) - t
        for x in nums:
            while stack and drop > 0 and stack[-1] < x:
                stack.pop()
                drop -= 1
            stack.append(x)
        return stack[:t]

    def merge(a, b):
        # Custom max-merge: at each step pick the larger lookahead prefix.
        res = []
        i = j = 0
        total = len(a) + len(b)
        for _ in range(total):
            if i == len(a):
                res.append(b[j]); j += 1
            elif j == len(b):
                res.append(a[i]); i += 1
            else:
                # Compare remaining slices to decide which head is larger.
                if a[i:] > b[j:]:
                    res.append(a[i]); i += 1
                else:
                    res.append(b[j]); j += 1
        return res

    best = None
    lo = max(0, k - len(nums2))
    hi = min(k, len(nums1))
    for i in range(lo, hi + 1):
        pick1 = max_subseq(nums1, i)
        pick2 = max_subseq(nums2, k - i)
        merged = merge(pick1, pick2)
        if best is None or merged > best:
            best = merged
    return best


CASES = [
    {"nums1": [3, 4, 6, 5], "nums2": [9, 1, 2, 5, 8, 3], "k": 5},
    {"nums1": [6, 7], "nums2": [6, 0, 4], "k": 5},
    {"nums1": [3, 9], "nums2": [8, 9], "k": 3},
    {"nums1": [1, 2, 3, 4, 5], "nums2": [6, 7, 8, 9, 10][:0], "k": 3},
    {"nums1": [9, 1, 2, 5, 8, 3], "nums2": [3, 4, 6, 5], "k": 5},
    {"nums1": [5, 5, 1], "nums2": [4, 0, 1], "k": 3},
    {"nums1": [2, 5, 6, 4, 4, 0], "nums2": [7, 3, 8, 0, 6, 5, 7, 6, 2], "k": 15},
    {"nums1": [1], "nums2": [2], "k": 2},
]


if __name__ == '__main__':
    import json
    out = []
    for idx, c in enumerate(CASES):
        result = solve(c["nums1"], c["nums2"], c["k"])
        out.append({
            "id": idx,
            "input": c,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
