import json
from collections import deque

def solve(n, op_seq):
    q = deque()
    result = []
    for t in op_seq:
        q.append(t)
        while q and q[0] < t - 3000:
            q.popleft()
        result.append(len(q))
    return result

CASES = [
    {"n": 4, "op_seq": [1, 100, 3001, 3002]},
    {"n": 1, "op_seq": [1]},
    {"n": 3, "op_seq": [1, 2, 3]},
    {"n": 5, "op_seq": [1, 100, 1000, 3001, 3100]},
    {"n": 6, "op_seq": [10, 20, 3010, 3020, 6000, 6001]},
    {"n": 4, "op_seq": [3000, 3001, 3002, 5999]},
    {"n": 3, "op_seq": [1, 3001, 3002]},
    {"n": 2, "op_seq": [2999, 3000]},
]

if __name__ == '__main__':
    output = []
    for i, case in enumerate(CASES):
        result = solve(case["n"], case["op_seq"])
        output.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(output, separators=(',', ':'), ensure_ascii=False))
