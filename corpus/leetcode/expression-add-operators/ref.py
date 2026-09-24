import json
from typing import List

def solve(num: str, target: int) -> List[str]:
    n = len(num)
    res: List[str] = []

    def backtrack(index: int, path: str, value: int, prev_term: int):
        if index == n:
            if value == target:
                res.append(path)
            return
        for i in range(index, n):
            if i != index and num[index] == '0':
                break
            curr_str = num[index:i+1]
            curr = int(curr_str)
            if index == 0:
                backtrack(i+1, curr_str, curr, curr)
            else:
                # addition
                backtrack(i+1, path + '+' + curr_str, value + curr, curr)
                # subtraction
                backtrack(i+1, path + '-' + curr_str, value - curr, -curr)
                # multiplication
                backtrack(i+1, path + '*' + curr_str, value - prev_term + prev_term * curr, prev_term * curr)

    backtrack(0, "", 0, 0)
    return res


CASES = [
    {"num": "123", "target": 6},
    {"num": "232", "target": 8},
    {"num": "105", "target": 5},
    {"num": "00", "target": 0},
    {"num": "3456237490", "target": 9191},
    {"num": "1", "target": 1},
    {"num": "1000000000", "target": 0},
    {"num": "2147483647", "target": 2147483647},
]

if __name__ == '__main__':
    out = []
    for i, case in enumerate(CASES):
        result = solve(case["num"], case["target"])
        canonical = json.dumps(sorted(result), separators=(',', ':'), ensure_ascii=False)
        out.append({
            "id": i,
            "input": {"num": case["num"], "target": case["target"]},
            "expected": canonical
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
