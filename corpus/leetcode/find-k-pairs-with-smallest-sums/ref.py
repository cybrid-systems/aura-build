import json
import heapq

def solve(nums1: list[int], nums2: list[int], k: int) -> list[tuple[int, int]]:
    if not nums1 or not nums2 or k == 0:
        return []
    n1, n2 = len(nums1), len(nums2)
    # Seed heap with at most min(k, n1) pairs (i, 0)
    heap = []
    initial = min(k, n1)
    for i in range(initial):
        heapq.heappush(heap, (nums1[i] + nums2[0], i, 0))
    result = []
    while heap and len(result) < k:
        s, i, j = heapq.heappop(heap)
        result.append((nums1[i], nums2[j]))
        if j + 1 < n2:
            heapq.heappush(heap, (nums1[i] + nums2[j + 1], i, j + 1))
    return result


CASES = [
    {"nums1": [1, 7, 11], "nums2": [2, 4, 6], "k": 3},
    {"nums1": [1, 7, 11], "nums2": [2, 4, 6], "k": 10},
    {"nums1": [1, 2], "nums2": [3], "k": 3},
    {"nums1": [], "nums2": [1, 2, 3], "k": 5},
    {"nums1": [1, 1, 2], "nums2": [1, 2, 3], "k": 2},
    {"nums1": [1, 2, 3, 4], "nums2": [1, 2, 3, 4], "k": 1},
    {"nums1": [5, 6, 7], "nums2": [1, 2, 3], "k": 5},
    {"nums1": [1, 1, 1], "nums2": [1, 1, 1], "k": 4},
]


if __name__ == '__main__':
    out = []
    for i, c in enumerate(CASES):
        res = solve(c["nums1"], c["nums2"], c["k"])
        canonical = json.dumps(res, separators=(',', ':'), ensure_ascii=False)
        out.append({"id": i, "input": c, "expected": canonical})
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
