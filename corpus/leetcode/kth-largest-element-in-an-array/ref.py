import sys
import json
import random

def quickselect(nums, k):
    """Find k-th largest (1-indexed) using quickselect. Expected O(n)."""
    arr = list(nums)
    target = k  # we want k-th largest, i.e., element at index n-k in sorted ascending
    n = len(arr)
    # We'll work with indices into arr and select based on ascending rank.
    # k-th largest == (n - k)-th smallest (0-indexed)
    rank = n - k  # 0-indexed rank in ascending order

    lo, hi = 0, n - 1
    while lo < hi:
        # Median-of-three pivot to avoid worst case
        mid = (lo + hi) // 2
        if arr[lo] > arr[mid]:
            arr[lo], arr[mid] = arr[mid], arr[lo]
        if arr[lo] > arr[hi]:
            arr[lo], arr[hi] = arr[hi], arr[lo]
        if arr[mid] > arr[hi]:
            arr[mid], arr[hi] = arr[hi], arr[mid]
        pivot = arr[mid]
        # Move pivot to end
        arr[mid], arr[hi] = arr[hi], arr[mid]
        # Partition
        i = lo
        for j in range(lo, hi):
            if arr[j] < pivot:
                arr[i], arr[j] = arr[j], arr[i]
                i += 1
        arr[i], arr[hi] = arr[hi], arr[i]
        if rank < i:
            hi = i - 1
        elif rank > i:
            lo = i + 1
        else:
            return arr[i]
    return arr[lo]

def solve(nums, k):
    return quickselect(nums, k)

CASES = [
    {"id": 0, "input": {"nums": [3, 2, 1, 5, 6, 4], "k": 2}, "expected": None},
    {"id": 1, "input": {"nums": [3, 2, 3, 1, 2, 4, 5, 5, 6], "k": 4}, "expected": None},
    {"id": 2, "input": {"nums": [1], "k": 1}, "expected": None},
    {"id": 3, "input": {"nums": [-1, -2, -3, -4, -5], "k": 1}, "expected": None},
    {"id": 4, "input": {"nums": [7, 7, 7, 7], "k": 4}, "expected": None},
    {"id": 5, "input": {"nums": [2, 1], "k": 2}, "expected": None},
    {"id": 6, "input": {"nums": [5, 4, 3, 2, 1], "k": 5}, "expected": None},
    {"id": 7, "input": {"nums": [10, -10, 0, 100, -100, 50, 50], "k": 3}, "expected": None},
]

if __name__ == '__main__':
    rng = random.Random(42)
    extra = [rng.randint(-100, 100) for _ in range(20)]
    CASES.append({"id": 8, "input": {"nums": extra, "k": 7}, "expected": None})

    out = []
    for case in CASES:
        nums = case["input"]["nums"]
        k = case["input"]["k"]
        result = solve(nums, k)
        out.append({
            "id": case["id"],
            "input": {"nums": nums, "k": k},
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
