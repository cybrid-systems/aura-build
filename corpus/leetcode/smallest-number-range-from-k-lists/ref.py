import heapq
import json

def solve(k, n, lists):
    if k == 1:
        # Only one list: smallest range covering it is a single point at min
        return [lists[0][0], lists[0][0]]
    
    heap = []
    current_max = float('-inf')
    # Initialize heap with first element from each list
    for i in range(k):
        val = lists[i][0]
        heapq.heappush(heap, (val, i, 0))
        if val > current_max:
            current_max = val
    
    best_a = float('inf')
    best_b = float('inf')
    best_len = float('inf')
    
    while True:
        cur_min, list_idx, pos = heap[0]
        cur_range_len = current_max - cur_min
        # Update best: prefer shorter, then smaller start
        if (cur_range_len < best_len or 
            (cur_range_len == best_len and cur_min < best_a)):
            best_len = cur_range_len
            best_a = cur_min
            best_b = current_max
        
        # Try to advance in the list that gave us the minimum
        next_pos = pos + 1
        if next_pos >= n:
            break  # Can't advance; one list exhausted
        
        next_val = lists[list_idx][next_pos]
        heapq.heapreplace(heap, (next_val, list_idx, next_pos))
        if next_val > current_max:
            current_max = next_val
    
    return [best_a, best_b]


CASES = [
    {
        "id": 0,
        "k": 3, "n": 5,
        "lists": [
            [1, 5, 10, 13, 21],
            [2, 6, 12, 19, 25],
            [3, 8, 15, 24, 26]
        ]
    },
    {
        "id": 1,
        "k": 1, "n": 4,
        "lists": [
            [4, 10, 15, 24]
        ]
    },
    {
        "id": 2,
        "k": 2, "n": 3,
        "lists": [
            [1, 2, 3],
            [4, 5, 6]
        ]
    },
    {
        "id": 3,
        "k": 2, "n": 3,
        "lists": [
            [1, 5, 9],
            [2, 3, 10]
        ]
    },
    {
        "id": 4,
        "k": 3, "n": 3,
        "lists": [
            [1, 2, 3],
            [1, 2, 3],
            [1, 2, 3]
        ]
    },
    {
        "id": 5,
        "k": 2, "n": 2,
        "lists": [
            [0, 100],
            [1, 2]
        ]
    },
    {
        "id": 6,
        "k": 4, "n": 3,
        "lists": [
            [1, 4, 7],
            [2, 5, 8],
            [3, 6, 9],
            [0, 10, 20]
        ]
    },
]


if __name__ == '__main__':
    results = []
    for case in CASES:
        k = case["k"]
        n = case["n"]
        lists = case["lists"]
        result = solve(k, n, lists)
        expected = json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        results.append({
            "id": case["id"],
            "input": {"k": k, "n": n, "lists": lists},
            "expected": expected
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
