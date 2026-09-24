import sys
import json

def solve(target: int, matrix: list[list[int]]) -> bool:
    if not matrix or not matrix[0]:
        return False
    m = len(matrix)
    n = len(matrix[0])
    lo, hi = 0, m * n - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        r, c = divmod(mid, n)
        val = matrix[r][c]
        if val == target:
            return True
        elif val < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return False

CASES = [
    {"target": 5, "matrix": [[1,3,5,7],[10,11,16,20],[23,30,34,60]]},
    {"target": 13, "matrix": [[1,3,5,7],[10,11,16,20],[23,30,34,60]]},
    {"target": 1, "matrix": [[1,3,5,7],[10,11,16,20],[23,30,34,60]]},
    {"target": 60, "matrix": [[1,3,5,7],[10,11,16,20],[23,30,34,60]]},
    {"target": 0, "matrix": [[1,3,5,7],[10,11,16,20],[23,30,34,60]]},
    {"target": 7, "matrix": [[7]]},
    {"target": 2, "matrix": [[1,2,3]]},
    {"target": 3, "matrix": [[1],[3],[5]]},
    {"target": 4, "matrix": [[1],[3],[5]]},
    {"target": 1, "matrix": [[]]},
    {"target": 1, "matrix": []},
]

def parse_input():
    data = {}
    for line in sys.stdin:
        line = line.strip()
        if not line.startswith("CASE0="):
            continue
        body = line[len("CASE0="):]
        if "=" not in body:
            continue
        key, val = body.split("=", 1)
        if key == "target":
            data["target"] = int(val)
        elif key.startswith("row"):
            arr = json.loads(val)
            data.setdefault("matrix", []).append(arr)
        elif key == "matrix":
            parts = val.split("x")
            data["rows"] = int(parts[0])
            data["cols"] = int(parts[1])
    return data.get("target"), data.get("matrix", [])

if __name__ == '__main__':
    out = []
    for i, case in enumerate(CASES):
        result = solve(case["target"], case["matrix"])
        out.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
