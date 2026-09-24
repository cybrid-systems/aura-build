import json
import heapq

def solve(lists):
    heap = []
    for i, lst in enumerate(lists):
        if lst:
            heapq.heappush(heap, (lst[0], i, 0))
    
    result = []
    while heap:
        val, i, j = heapq.heappop(heap)
        result.append(val)
        if j + 1 < len(lists[i]):
            heapq.heappush(heap, (lists[i][j + 1], i, j + 1))
    
    return result

CASES = [
    {"lists": [[1, 4, 5], [1, 3, 4], [2, 6]]},
    {"lists": []},
    {"lists": [[], [], []]},
    {"lists": [[1, 2, 3]]},
    {"lists": [[1], [2], [3], [4], [5]]},
    {"lists": [[5, 10, 15], [1, 2, 3], [7, 8, 9]]},
    {"lists": [[-5, -2], [-3, 0, 4], [-1, 1, 6]]},
    {"lists": [[1, 1, 1], [2, 2, 2], [3, 3, 3]]},
]

if __name__ == '__main__':
    output = []
    for idx, case in enumerate(CASES):
        result = solve(**case)
        output.append({"id": idx, "input": case, "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(output, separators=(',', ':'), ensure_ascii=False))
