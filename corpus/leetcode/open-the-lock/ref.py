from collections import deque
import json

def solve(N: int, target: str, deadends: list[str]) -> int:
    if "0000" in deadends:
        return -1
    forbidden = set(deadends)
    if "0000" in forbidden:
        return -1
    visited = {"0000"}
    q = deque([("0000", 0)])
    while q:
        cur, d = q.popleft()
        if cur == target:
            return d
        # 8 +/- 1 neighbors
        for i in range(4):
            d_int = int(cur[i])
            for nd in ((d_int + 1) % 10, (d_int - 1) % 10):
                ns = cur[:i] + str(nd) + cur[i+1:]
                if ns not in visited and ns not in forbidden:
                    visited.add(ns)
                    q.append((ns, d + 1))
        # 9 free-set neighbors for each dial (set to any other digit)
        for i in range(4):
            orig = cur[i]
            for nd in range(10):
                if nd == orig:
                    continue
                ns = cur[:i] + str(nd) + cur[i+1:]
                if ns not in visited and ns not in forbidden:
                    visited.add(ns)
                    q.append((ns, d + 1))
    return -1

CASES = [
    {"N": 5, "target": "0202", "deadends": ["0201","0101","0102","1212","2002"]},
    {"N": 0, "target": "0001", "deadends": []},
    {"N": 0, "target": "1111", "deadends": []},
    {"N": 1, "target": "0001", "deadends": ["0000"]},
    {"N": 4, "target": "0123", "deadends": ["0001","0010","0100","1000"]},
    {"N": 2, "target": "0009", "deadends": ["0008","0007"]},
    {"N": 3, "target": "9999", "deadends": ["0009","0099","0999"]},
    {"N": 1, "target": "1234", "deadends": ["1234"]},
]

if __name__ == '__main__':
    out = []
    for i, c in enumerate(CASES):
        result = solve(c["N"], c["target"], c["deadends"])
        out.append({"id": i, "input": c, "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
