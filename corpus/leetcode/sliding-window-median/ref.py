import heapq
import json
from typing import List

def solve(nums: List[int], k: int) -> List[int]:
    if k == 0 or not nums:
        return []
    
    # max-heap for lower half (store negatives)
    # min-heap for upper half
    lo = []  # max-heap (negated)
    hi = []  # min-heap
    
    # Maps for lazy deletion
    # Since values can be duplicate, we need to track counts to delete
    from collections import Counter
    delayed = Counter()
    
    def prune(heap):
        while heap:
            if heap is lo:
                val = -heap[0]
                if delayed[val] > 0:
                    heapq.heappop(heap)
                    delayed[val] -= 1
                    if delayed[val] == 0:
                        del delayed[val]
                else:
                    break
            else:
                val = heap[0]
                if delayed[val] > 0:
                    heapq.heappop(heap)
                    delayed[val] -= 1
                    if delayed[val] == 0:
                        del delayed[val]
                else:
                    break
    
    def balance():
        # Ensure len(lo) >= len(hi) and len(lo) - len(hi) <= 1
        # Or more precisely:
        # if k is odd: len(lo) = (k+1)//2, len(hi) = k//2
        # if k is even: len(lo) = len(hi) = k//2
        # General invariant: len(lo) >= len(hi) and len(lo) <= len(hi) + 1
        prune(lo)
        prune(hi)
        if len(lo) > len(hi) + 1:
            val = -heapq.heappop(lo)
            heapq.heappush(hi, val)
            prune(lo)
        elif len(lo) < len(hi):
            val = heapq.heappop(hi)
            heapq.heappush(lo, -val)
            prune(hi)
    
    # Initialize first window
    for i in range(k):
        num = nums[i]
        if not lo or num <= -lo[0]:
            heapq.heappush(lo, -num)
        else:
            heapq.heappush(hi, num)
        balance()
    
    result = []
    
    def get_median():
        if k % 2 == 1:
            return -lo[0]
        else:
            return -lo[0] + hi[0]
    
    result.append(get_median())
    
    # Slide window
    for i in range(k, len(nums)):
        # Add nums[i]
        num_in = nums[i]
        if lo and num_in <= -lo[0]:
            heapq.heappush(lo, -num_in)
        else:
            heapq.heappush(hi, num_in)
        balance()
        
        # Remove nums[i - k]
        num_out = nums[i - k]
        delayed[num_out] += 1
        if lo and num_out <= -lo[0]:
            prune(lo)
        else:
            prune(hi)
        balance()
        
        result.append(get_median())
    
    return result


CASES = [
    {"nums": [1, 3, -1, -3, 5, 3, 6, 7], "k": 3},
    {"nums": [1, 3, -1, -3, 5, 3, 6, 7], "k": 2},
    {"nums": [1, 3, -1, -3, 5, 3, 6, 7], "k": 1},
    {"nums": [1, 3, -1, -3, 5, 3, 6, 7], "k": 4},
    {"nums": [1], "k": 1},
    {"nums": [2, 2, 2, 2], "k": 2},
    {"nums": [5, 4, 3, 2, 1], "k": 3},
    {"nums": [1, 2, 3, 4, 5, 6, 7, 8], "k": 4},
]


if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        nums = case["nums"]
        k = case["k"]
        result = solve(nums, k)
        results.append({
            "id": i,
            "input": {"nums": nums, "k": k},
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
