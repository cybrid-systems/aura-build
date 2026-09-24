import sys
import json
from typing import List

def solve(nums1: List[int], nums2: List[int]) -> float:
    # Ensure nums1 is the smaller array for efficient binary search
    if len(nums1) > len(nums2):
        nums1, nums2 = nums2, nums1
    
    m, n = len(nums1), len(nums2)
    total = m + n
    half = (total + 1) // 2
    
    lo, hi = 0, m
    
    while lo <= hi:
        mid1 = (lo + hi) // 2
        mid2 = half - mid1
        
        # Left and right elements of each partition
        left1 = float('-inf') if mid1 == 0 else nums1[mid1 - 1]
        right1 = float('inf') if mid1 == m else nums1[mid1]
        left2 = float('-inf') if mid2 == 0 else nums2[mid2 - 1]
        right2 = float('inf') if mid2 == n else nums2[mid2]
        
        # Check if partition is correct
        if left1 <= right2 and left2 <= right1:
            # Found correct partition
            if total % 2 == 1:
                return float(max(left1, left2))
            else:
                return (max(left1, left2) + min(right1, right2)) / 2.0
        elif left1 > right2:
            # Too many elements from nums1, move left
            hi = mid1 - 1
        else:
            # Too few elements from nums1, move right
            lo = mid1 + 1
    
    # Should never reach here with valid inputs
    raise ValueError("Input arrays are not sorted or invalid")

CASES = [
    {"nums1": [1, 3], "nums2": [2]},
    {"nums1": [1, 2], "nums2": [3, 4]},
    {"nums1": [], "nums2": [1]},
    {"nums1": [0, 0], "nums2": [0, 0]},
    {"nums1": [1], "nums2": [2, 3, 4, 5, 6]},
    {"nums1": [-5, -3, -1], "nums2": [-2, 0, 4]},
    {"nums1": [1, 2, 3, 4, 5], "nums2": [6, 7, 8, 9, 10]},
    {"nums1": [1, 1, 1], "nums2": [1, 1, 1, 1]},
]

if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        result = solve(case["nums1"], case["nums2"])
        results.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
