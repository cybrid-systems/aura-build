import json
import sys

def solve(nums):
    if len(nums) < 2:
        return 0
    # Build bitwise trie
    trie = {}
    for num in nums:
        node = trie
        for i in range(30, -1, -1):
            bit = (num >> i) & 1
            if bit not in node:
                node[bit] = {}
            node = node[bit]
        # store the value at the leaf
        node['val'] = num
    # For each num, find best complement
    best = 0
    for num in nums:
        node = trie
        path = []
        cur = trie
        for i in range(30, -1, -1):
            bit = (num >> i) & 1
            opp = 1 - bit
            if opp in cur:
                cur = cur[opp]
                path.append(1)
            else:
                cur = cur[bit]
                path.append(0)
        # cur is leaf, get the other number
        other = cur['val']
        best = max(best, num ^ other)
    return best

CASES = [
    {"nums": [4, 1, 2, 3]},
    {"nums": [8, 10, 2]},
    {"nums": [0, 0]},
    {"nums": [5]},
    {"nums": []},
    {"nums": [1, 2, 3, 4, 5, 6, 7, 8]},
    {"nums": [0, 2147483647]},
    {"nums": [1000000000, 999999999, 1, 2]},
]

if __name__ == '__main__':
    out = []
    for i, case in enumerate(CASES):
        result = solve(case["nums"])
        out.append({"id": i, "input": case, "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)})
    sys.stdout.write(json.dumps(out, ensure_ascii=False))
